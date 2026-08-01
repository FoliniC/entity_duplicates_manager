#!/usr/bin/env python3
"""
Tenda Mesh Client Monitor
=========================
Monitora a quale nodo (Base/Satellite) è connesso un client specifico
nel Tenda MW5 Mesh. Logga su file e opzionalmente notifica Home Assistant.

Requisiti:
- SSH access al router OpenWrt (192.168.0.11) con chiave
- Tenda base IP: 192.168.0.10 (interfaccia web)
- MAC target: 50:8b:b9:44:fe:4e (luci-cucina)

Metodi di rilevamento (in ordine di preferenza):
1. Tenda Web API (se accessibile) - più accurato, dice esattamente Base vs Satellite
2. OpenWrt iwinfo/hostapd assoclist - vede su quale radio fisica arriva il traffico
3. ARP + nftables counters - indiretto, vede solo attività

Output:
- File log: /config/logs/tenda_roam_monitor.log
- Notifica HA via webhook (opzionale)
- Stato entity HA: sensor.tenda_luci_cucina_ap (opzionale)
"""

import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── CONFIG ──────────────────────────────────────────────────────────────────
TARGET_MAC = "50:8b:b9:44:fe:4e"          # luci-cucina (bf054a2177fd16678d9yds)
TARGET_IP = "192.168.0.25"
TARGET_NAME = "luci-cucina"

TENDA_BASE_IP = "192.168.0.10"
TENDA_WEB_URL = f"http://{TENDA_BASE_IP}"

OPENWRT_HOST = "192.168.0.11"
OPENWRT_USER = "root"
SSH_KEY = "/home/carlo/docker/homeassistant/config/.ssh/router_key"  # chiave SSH per root@OpenWrt

# Percorsi (host path - in container HA è /config/logs/)
LOG_DIR = Path("/home/carlo/docker/homeassistant/config/logs")
LOG_FILE = LOG_DIR / "tenda_roam_monitor.log"
STATE_FILE = LOG_DIR / "tenda_roam_state.json"
CHECK_INTERVAL = 30                         # secondi
NOTIFY_ON_CHANGE = True

# Home Assistant webhook (opzionale) - imposta URL se vuoi notifiche
HA_WEBHOOK_URL = None  # es: "http://192.168.0.3:8123/api/webhook/tenda_roam"
HA_ENTITY_ID = "sensor.tenda_luci_cucina_ap"  # entity da aggiornare via service call

# ─── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ─── SESSION HTTP con retry ──────────────────────────────────────────────────
def make_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

SESSION = make_session()

# ─── UTILITY ─────────────────────────────────────────────────────────────────
def run_ssh(cmd: str, timeout: int = 10) -> tuple[int, str, str]:
    """Esegue comando SSH su OpenWrt."""
    full_cmd = ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "ConnectTimeout=5",
                f"{OPENWRT_USER}@{OPENWRT_HOST}", cmd]
    try:
        r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_ap": None, "last_seen": None, "history": []}

def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def notify_ha(message: str, ap_name: str):
    """Manda notifica a Home Assistant via webhook o service call."""
    if HA_WEBHOOK_URL:
        try:
            SESSION.post(HA_WEBHOOK_URL, json={
                "device": TARGET_NAME,
                "mac": TARGET_MAC,
                "ap": ap_name,
                "message": message,
                "time": datetime.now().isoformat(),
            }, timeout=5)
        except Exception as e:
            log.warning(f"HA webhook failed: {e}")

def update_ha_entity(ap_name: str):
    """Aggiorna sensor HA via REST API (richiede token)."""
    # Da implementare se hai long-lived token
    pass

# ─── METODO 1: TENDA WEB INTERFACE ───────────────────────────────────────────
def get_ap_from_tenda_web() -> Optional[str]:
    """
    Tenta di leggere la client list dalla web UI Tenda.
    Tenda MW5 usa endpoint tipo /goform/GetClientList o simile.
    """
    endpoints_to_try = [
        "/goform/GetClientList",
        "/goform/getClientList",
        "/api/client/list",
        "/cgi-bin/luci/api/client/list",  # se ha OpenWrt
        "/goform/DeviceList",
        "/goform/getDeviceList",
    ]
    for ep in endpoints_to_try:
        try:
            r = SESSION.get(f"{TENDA_WEB_URL}{ep}", timeout=5)
            if r.status_code == 200:
                data = r.json() if r.headers.get("content-type", "").startswith("application") else r.text
                # Parsing generico: cerca MAC nel JSON/HTML
                if isinstance(data, dict):
                    clients = data.get("clientList") or data.get("devices") or data.get("list") or []
                    if isinstance(clients, list):
                        for c in clients:
                            mac = (c.get("mac") or c.get("MAC") or c.get("Mac") or "").lower()
                            if mac == TARGET_MAC.lower():
                                # Cerca campo che indica AP: "ap", "node", "parent", "signal", "online"
                                ap = (c.get("ap") or c.get("node") or c.get("parent") or
                                      c.get("apName") or c.get("parentName") or c.get("signal"))
                                if ap:
                                    return str(ap)
                                return "Tenda (unknown node)"
                elif isinstance(data, str):
                    # HTML scraping fallback
                    if TARGET_MAC.lower() in data.lower():
                        return "Tenda (found in HTML)"
        except Exception:
            continue
    return None

# ─── METODO 2: OPENWRT IWINFO / HOSTAPD ──────────────────────────────────────
def get_ap_from_openwrt() -> Optional[str]:
    """
    Su OpenWrt, controlla le associazioni su tutte le radio.
    Il Tenda base è collegato via cavo, ma i client wireless passano attraverso
    le radio del Tenda. Se il Tenda espone le sue radio come interfacce bridge
    su OpenWrt, possiamo vedere le associazioni.
    """
    # Lista radio (phy)
    code, out, _ = run_ssh("ls /sys/class/ieee80211/")
    if code != 0:
        return None
    phys = [p.strip() for p in out.split() if p.startswith("phy")]
    if not phys:
        return None

    for phy in phys:
        # iwinfo phyX assoclist
        code, out, _ = run_ssh(f"iwinfo {phy} assoclist")
        if code == 0 and TARGET_MAC.lower() in out.lower():
            # Parsa output per trovare signal/AP name
            # Output tipico: "50:8b:b9:44:fe:4e  -45 dBm  ...  (on wlan0)"
            lines = out.split("\n")
            for line in lines:
                if TARGET_MAC.lower() in line.lower():
                    # Estrai nome interfaccia (wlanX) che indica la radio
                    m = re.search(r"\(on\s+(\w+)\)", line)
                    iface = m.group(1) if m else phy
                    return f"OpenWrt:{iface} ({phy})"
    return None

# ─── METODO 3: ARP + NFTABLES (indiretto) ────────────────────────────────────
def get_activity_from_openwrt() -> Optional[str]:
    """
    Usa nftables counters esistenti (già attivi per realtime_per_device.py)
    per vedere se il device è attivo e su quale interfaccia fisica passa.
    """
    # Controlla contatori nftables per l'IP
    code, out, _ = run_ssh(f"nft list table inet filter | grep -A2 -B2 '{TARGET_IP}'")
    if code == 0 and out:
        return f"Active (nftables)"
    return None

# ─── METODO 4: ARP TABLE CHANGES (rileva roaming indiretto) ──────────────────
def get_arp_gateway_mac() -> Optional[str]:
    """
    Su OpenWrt, guarda la tabella ARP per vedere il MAC del gateway
    che risponde per l'IP del device. Se il device fa roaming,
    il MAC del next-hop potrebbe cambiare (base vs satellite).
    """
    code, out, _ = run_ssh(f"ip neigh show {TARGET_IP}")
    if code == 0 and out:
        # Output: "192.168.0.25 dev br-lan lladdr 50:8b:b9:44:fe:4e REACHABLE"
        # Il MAC lladdr è del device, non dell'AP. Ma se c'è proxy ARP...
        pass
    return None

# ─── MAIN DETECTION LOGIC ────────────────────────────────────────────────────
def detect_current_ap() -> tuple[str, str]:
    """
    Ritorna (ap_name, method)
    ap_name: stringa identificativa (es. "Tenda-Base", "Satellite-1", "Unknown")
    method: quale metodo ha funzionato
    """
    # 1. Tenda Web (più accurato)
    ap = get_ap_from_tenda_web()
    if ap:
        return ap, "tenda_web"

    # 2. OpenWrt iwinfo (se radio visibili)
    ap = get_ap_from_openwrt()
    if ap:
        return ap, "openwrt_iwinfo"

    # 3. Activity check
    ap = get_activity_from_openwrt()
    if ap:
        return ap, "nftables_activity"

    return "Unknown", "none"

# ─── MAIN LOOP ───────────────────────────────────────────────────────────────
def main():
    log.info(f"Starting Tenda roam monitor for {TARGET_NAME} ({TARGET_MAC})")
    log.info(f"Log file: {LOG_FILE}")
    log.info(f"State file: {STATE_FILE}")

    state = load_state()
    last_ap = state.get("last_ap")

    while True:
        try:
            ap_name, method = detect_current_ap()
            now = datetime.now().isoformat()

            log.info(f"Check: AP={ap_name} | Method={method}")

            # Cambio rilevato
            if ap_name != last_ap and last_ap is not None:
                msg = f"🔄 ROAM DETECTED: {TARGET_NAME} moved from '{last_ap}' to '{ap_name}'"
                log.warning(msg)
                if NOTIFY_ON_CHANGE:
                    notify_ha(msg, ap_name)
                    update_ha_entity(ap_name)

                # Storico
                history = state.get("history", [])
                history.append({
                    "time": now,
                    "from": last_ap,
                    "to": ap_name,
                    "method": method,
                })
                # Mantieni solo ultimi 100
                state["history"] = history[-100:]

            # Aggiorna stato
            state["last_ap"] = ap_name
            state["last_seen"] = now
            state["last_method"] = method
            save_state(state)

        except KeyboardInterrupt:
            log.info("Stopped by user")
            break
        except Exception as e:
            log.error(f"Error in main loop: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()