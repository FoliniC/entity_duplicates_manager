# USB Tethering - Documentazione Completa e Consolidata

**Data:** 2026-10-19  
**Ambiente:** Home Assistant su Debian 13 (192.168.0.3) + Router OpenWrt (192.168.0.11) + Desktop Windows 11 (192.168.0.8)  
**Versione:** 2.0 — Consolidato da file multipli, include sviluppi fino a Ottobre 2026

---

## 📋 Executive Summary

Il sistema gestisce **tre modalità di connessione Internet** tramite tethering USB di smartphone Android, commutabili da Home Assistant:

| Modalità | Telefono | Host USB | Gateway Internet | Descrizione |
|----------|----------|----------|------------------|-------------|
| **Normale** | Redmi Note 11 Pro 5G (`veux`) | Router (`192.168.0.11`) | `usb0` del router (metric 10) | WAN standard del router via telefono sul router |
| **Server** | Redmi Note 13 Pro 5G | Debian (`192.168.0.3`) | Telefono su Debian (metric 50) | Debian usa proprio telefono come gateway, LAN via router |
| **Intranet** | Redmi Note 13 Pro 5G | Debian (`192.168.0.3`) | Telefono su Debian + NAT per LAN | Debian fa da ponte NAT per **tutta la LAN** (router → Debian → telefono) |

**Telefoni attuali (Ottobre 2026):**
- **Router (Note 11 Pro 5G / `veux`)**: ADB serial `69a47f6d3a61`, collegato USB al router OpenWrt
- **Debian (Note 13 Pro 5G / Xiaomi 17 Ultra)**: collegato USB a Debian, interfaccia `enx*` rilevata dinamicamente

---

## 🔌 Architettura di Rete e Routing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOME NETWORK (192.168.0.0/24)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌────────────────┐     ┌────────────────────────┐   │
│  │ HA Server    │     │  Router        │     │  Phone Router (veux)   │   │
│  │ (Debian)     │◄────│  (OpenWrt)     │◄────│  Redmi Note 11 Pro 5G  │   │
│  │ 192.168.0.3  │     │  192.168.0.11  │     │  usb0: 10.203.33.x/24  │   │
│  └──────────────┘     └────────────────┘     └────────────────────────┘   │
│        │                     │                        │                    │
│        │              usb0 (WAN)              USB tethering               │
│        │              metric 10                 RNDIS                     │
│        │                     │                        │                    │
│        │              ┌──────────────┐                            │        │
│        │              │   br-lan     │◄── anchor Intranet         │        │
│        │              │  metric 9    │     (via Debian)           │        │
│        │              └──────────────┘                            │        │
│        │                                                           │        │
│        ▼                                                           │        │
│  ┌─────────────────────┐                                           │        │
│  │ Phone Debian        │                                           │        │
│  │ (Xiaomi 17 Ultra)   │                                           │        │
│  │ enx*: 10.157.77.x   │                                           │        │
│  └─────────────────────┘                                           │        │
│        │                                                           │        │
│        ▼                                                           │        │
│  ┌─────────────────────┐                                           │        │
│  │ Desktop Windows 11  │                                           │        │
│  │ 192.168.0.8         │                                           │        │
│  └─────────────────────┘                                           │        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Comportamento atteso per device (chi esce da dove)

| Device | Modalità Normale | Modalità Server | Modalità Intranet |
|--------|------------------|-----------------|-------------------|
| **Debian (192.168.0.3)** | Proprio telefono USB (metric ~103) | Proprio telefono USB (metric 50) | Proprio telefono USB + MASQUERADE per LAN |
| **Router (192.168.0.11)** | WAN `usb0` (Note 11 sul router) | Fallback → Debian (br-lan metric 9) | Anchor Debian (br-lan metric 9) |
| **LAN / Windows (192.168.0.8)** | Router → WAN (se attiva) altrimenti **isolata** | Router → Debian (fallback) | Router → Debian → telefono (tutta LAN via Debian) |

> **Verifica rapida**: In Normale, `ip route show default` sul router deve mostrare `usb0` (non `192.168.0.3 dev br-lan metric 9`). Se mostra l'anchor Debian significa che il restore non è completato.

---

## 🛠️ Script e Componenti Chiave

### 1. Script Router OpenWrt (`/usr/bin/`)

| Script | Funzione | Note |
|--------|----------|------|
| `enable_usb_tether.sh` | Attiva RNDIS via ADB UI automation (`input tap`) | Fragile su MIUI, coordinate hardcoded |
| `check_and_restore_android_tether.sh` | **Check/restore robusto** — verifica `sys.usb.config`, `usb0` IP, route, ping | **Nuovo (Ott 2026)** — sostituisce UI automation per controlli periodici |
| `check_note11_router.sh` | Check connettività Note 11 (exit codes: 1=ADB_UNAUTH, 2=NO_RNDIS, 3=NO_USB0_IP, 4=GATEWAY_UNREACH, 0=OK) | Chiamato da systemd timer Debian |
| `streampack-rndis-configure.sh` | Configura Proxy ARP + nftables per StreamPack RTMP via alias IP dinamico | Hotplug `iface/97-streampack-rndis` |
| `tethering-graceful.sh` | Shutdown graceful WAN | Legacy |

### 2. Script Debian (`/home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh`)

Script principale per gestione tethering su Debian. Comandi:

```bash
usb_tether.sh detect               # Stampa IFACE|GW o vuoto (exit 1)
usb_tether.sh activate <max_min> [intranet|server]  # Attiva route + watcher (default 30')
usb_tether.sh restore              # Ripristina (idempotente)
usb_tether.sh status               # JSON stato (active/idle/error)
usb_tether.sh diagnose             # Troubleshooting completo
```

**Caratteristiche chiave:**
- Stato in `/run/usb_tether_state` (tmpfs, auto-heal al reboot)
- Watcher detached (`setsid`) per safety-net indipendente da HA
- `router_wan_down()` usa `ifdown wan` + `uci set network.wan.auto='0'` per bloccare netifd
- `router_wan_up()` usa `ifup wan` + `uci set network.wan.auto='1'`
- Anchor Intranet metric **9** (vince su `usb0 metric 10`)
- NAT/forwarding per traffico router → telefono (`enable_nat_router` / `disable_nat_router`)

### 3. Script Windows (`C:\Scripts\usb_tether.ps1`)

Parità funzionale con script Debian per modalità Intranet/Server da Windows 11.

### 4. Helper HA (`/config/helpers/usb_tether_ha.sh`)

Script unificato nel container HA che delega via SSH:
- SSH Multiplexing (`ControlMaster=auto`, `ControlPersist=60s`)
- Comandi async: ritorna `{"state":"activating"}` / `{"state":"restoring"}` subito
- Pre-flight check con **Error Marker Pattern** (vedi sotto)
- Gestisce Debian, Windows, Router

### 5. Systemd Timer Debian (`tether-check.timer`)

```ini
# /etc/systemd/user/tether-check.timer
[Unit]
Description=Check tethering status every 5 minutes
[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Persistent=true
[Install]
WantedBy=timers.target
```

Esegue `/home/carlo/bin/tether_check.sh` ogni 5 min, scrive `/config/tether_status.json` con stato router + Debian.

### 6. Package HA (`packages/usb_tether.yaml`)

Include:
- `input_select.usb_tether_mode` (normale/server/intranet)
- `input_select.usb_tether_host` (debian/windows)
- `input_number.usb_tether_max_duration`
- `input_text.usb_tether_note11_status` / `input_text.usb_tether_android_status` (stato dashboard)
- `sensor.usb_tether_status` (command_line, poll 60s, chiama `usb_tether_ha.sh status`)
- `sensor.tether_router_status` / `sensor.tether_debian_status` (command_line, leggono `tether_status.json`)
- Template sensors `sensor.internet_note_11_router` / `sensor.internet_android_debian` (stato OK/PROBLEMA/ERRORE/Non verificato)
- Automazioni: periodicità 5min, startup check, message preservation

---

## 🔄 Automazioni e Logica di Controllo

### 1. Verifica Periodica (`usb_tether_verifica_periodica` — ogni 5 min)

```yaml
trigger:
  - platform: time_pattern
    minutes: "/5"
action:
  - shell_command: check_android_tether    # SEMPRE: check/restore Note 11 su router
  - service: input_text.set_value          # Aggiorna input_text.usb_tether_note11_status
  - condition: template                    # SOLO se mode=Normale
      value_template: "{{ states('input_select.usb_tether_mode') == 'normale' }}"
  - shell_command: verify_tether_normale   # Verifica route primaria router
  - choose:                                # Correzione mode se mismatch
```

**Punti chiave:**
- Il check Android (Note 11 su router) gira **sempre**, indipendente dalla modalità HA
- La verifica route primaria gira **solo in Normale** per non forzare cambi in Intranet
- Aggiorna `input_text` direttamente (bypassa command_line scheduling issues)

### 2. Startup Check (`usb_tether_check_internet_startup_v4`)

```yaml
trigger:
  - platform: event
    event_type: homeassistant_started
action:
  - delay: "00:00:10"
  - shell_command: check_android_tether
  - service: homeassistant.update_entity   # Forza poll immediato sensori
    target:
      entity_id:
        - sensor.tether_router_status
        - sensor.tether_debian_status
```

Evita stati "unknown"/"IN_ATTESA" all'avvio HA.

### 3. Preservazione Messaggi Errore (Error Marker Pattern)

**Pre-flight in `activate` (`usb_tether_ha.sh`):**
```bash
ERROR_MARKER="/config/logs/usb_tether/last_error.marker"
detect_out=$(ssh_debian "sudo .../usb_tether.sh detect" 2>&1)
if (( $? != 0 )) || [[ -z "$detect_out" ]]; then
    printf '%s\n%s\n' "Tethering USB non disponibile..." "$(date '+%Y-%m-%d %H:%M:%S')" > "$ERROR_MARKER"
    json_error "Tethering USB non disponibile..."
    return 0
fi
rm -f "$ERROR_MARKER" 2>/dev/null || true
```

**Status check (`run_status`):**
```bash
if [[ -f "$ERROR_MARKER" ]]; then
    err_msg=$(head -1 "$ERROR_MARKER")
    err_time=$(sed -n '2p' "$ERROR_MARKER")
    printf '{"state":"error","mode":"%s","message":"%s (pre-flight fallito alle %s)"}\n' "$MODE" "$err_msg" "$err_time"
    return 0
fi
```

**Automation message cleanup (controlla TESTO non STATO):**
```yaml
- choose:
    - conditions:
        - condition: template
          value_template: "{{ 'ERRORE' in states('input_text.usb_tether_status_message') }}"
      sequence: []  # NON pulire se contiene ERRORE
    - conditions: []
      sequence:
        - action: input_text.set_value
          target:
            entity_id: input_text.usb_tether_status_message
          data:
            value: ""
```

---

## 📊 Sensori Dashboard (Tab "Tethering USB" + "Status Apparati")

### Sensori Sorgente
| Entity | Tipo | Source | Poll |
|--------|------|--------|------|
| `sensor.tether_router_status` | command_line | `/config/tether_status.json` → `.router.message` | 60s |
| `sensor.tether_debian_status` | command_line | `/config/tether_status.json` → `.debian.message` | 60s |

### Template Sensors (User-Friendly)
| Entity | Stato | Dettaglio (attributo) |
|--------|-------|----------------------|
| `sensor.internet_note_11_router` | `OK` / `PROBLEMA` / `ERRORE` | Messaggio completo da `tether_router_status` |
| `sensor.internet_android_debian` | `OK` / `PROBLEMA` / `ERRORE` / `Non verificato` | Messaggio completo da `tether_debian_status` |

**Logica estrazione stato:**
```jinja2
{% set msg = state_attr('sensor.tether_router_status', 'message') | default('') %}
{% set first_word = msg.split(' ')[0] %}
{{ first_word if first_word in ['OK','PROBLEMA','ERRORE'] else 'ERRORE' }}
```

### Dashboard Cards (Conditional Markdown)
- **Note 11 (Router)**: Verde se `OK`, arancione se `PROBLEMA`, rosso se `ERRORE`
- **Android (Debian)**: Verde se `OK`, arancione se `PROBLEMA`, rosso se `ERRORE`, **grigio + "Nessun tethering USB attivo su Debian..." se `Non verificato`**

---

## 🐛 Problemi Risolti e Fix Applicati (Cronologia)

### Fix Critici Agosto-Settembre 2026

| # | Problema | Root Cause | Fix Applicato | Data |
|---|----------|------------|---------------|------|
| 1 | Debian perde `192.168.0.3` su LAN | `systemd-networkd` disabilitato, NM non persistente | `enp2s0` statico via NM (`ipv4.method manual`, no gateway) | 29/08 |
| 2 | Bottone Intranet non applica NAT | Ramo idempotente ometteva `enable_nat_router` + non aggiornava `phone_if` in STATE_FILE | Ramo idempotente: rileva IF corrente, riapplica `router_wan_down` + anchor + NAT + riscrive STATE_FILE | 29/08 |
| 3 | `cmd_status` falliva in Intranet | Check metric 50 (solo Server) | Distinzione modalità: Intranet verifica IF UP + default route; Server verifica metric 50 | 29/08 |
| 4 | Passaggio Normale lascia sensore in Intranet | `cmd_restore` return 1 prima di pulire se WAN fallisce | `cmd_restore` **completa sempre**: rimuove anchor + pulisce stato + `router_wan_up` anche se WAN senza internet | 29/08 |
| 5 | Messaggio "in corso" appeso | Automazione preservava `"in corso"` anche a stato `idle` | Ordine `choose` ribaltato: `idle`/`active` puliscono sempre; `"in corso"` solo in transizione; `"ERRORE"` persiste | 29/08 |
| 6 | Watchdog HA non auto-recovery | Solo dump + Telegram, mai restart | `ha-watchdog.sh`: dump + `docker restart homeassistant` (cooldown 5min) + systemd service `Restart=always` | 29/08 |
| 7 | `btc_tracker` stalla HA | `hass.services.call('notify',...)` sincrono su event loop | `safe_notify()` con `hass.async_create_task(..., blocking=False)` | 29/08 |
| 8 | Restore background muore, STATE_FILE non rimosso | `setsid ... &` in `restore_debian` killed da HA shell_command timeout | `restore_debian` **foreground** (~49s), `shell_command.usb_tether_restore` timeout 120s | 29/08 |
| 9 | `adb tcpip 5555` resetta tethering RNDIS | Invocato ad ogni avvio `scrcpy-redmi.sh` anche se già TCP | Check `getprop service.adb.tcp.port` prima di `tcpip` | 29/09 |
| 10 | Dati mobile spenti bloccano Normale | `mobile_data=0` → bearer LTE down → WAN router morta | `router_wan_up` riaccende `mobile_data=1` + `svc data enable` + `svc usb setFunctions rndis` | 29/08 |
| 11 | Intranet activation timeout (60s) | `shell_command` 60s vs script 90s wait | Fire-and-forget: shell_command ritorna "activating" subito; script `wait_template` 2min su `sensor.usb_tether_status=active` | 19/10 |
| 12 | Route `usb0` stale su router in Intranet | `router_wan_down` non rimuoveva route esplicitamente | `router_wan_down`: `ip route del default dev usb0` + `ip link set usb0 down` | 19/10 |
| 13 | Dashboard mostra "NORMALE" in Intranet | Template leggeva attributo `mode` di `sensor.usb_tether_status` (poll 60s) | Priorità: `input_select.usb_tether_mode` (istantaneo) > attributo sensor | 19/10 |
| 14 | **Debian tethering non rilevato (Xiaomi 17 Ultra)** | `tether_check.sh` cercava solo `enx*` | Esteso detection a **qualsiasi interfaccia UP con IPv4 + gateway non-LAN** (esclude `enp2s0`, docker, veth, ecc.) | 19/10 |

---

## 🔧 Configurazioni Chiave e Comandi Operativi

### SSH Access
```bash
# Router OpenWrt
ssh -i /home/carlo/docker/homeassistant/config/.ssh/router_key \
    -o StrictHostKeyChecking=no \
    root@192.168.0.11

# Debian (loopback da container HA)
ssh -i /config/.ssh/host_key -o StrictHostKeyChecking=no carlo@localhost
```

### ADB Router Wrapper
```bash
# Sul router: /usr/bin/adb_router (MIPS, librerie in RAM)
ssh -i ... root@192.168.0.11 "/usr/bin/adb_router devices -l"
ssh -i ... root@192.168.0.11 "/usr/bin/adb_router -s 69a47f6d3a61 shell 'getprop sys.usb.config'"
```

### Comandi Verifica Rapida
```bash
# Stato tethering router (Note 11)
ssh -i ... root@192.168.0.11 "ip -br addr show dev usb0"
ssh -i ... root@192.168.0.11 "/usr/bin/check_and_restore_android_tether.sh"

# Stato tethering Debian (Xiaomi 17 Ultra)
ssh -i /config/.ssh/host_key carlo@localhost "ip -br link show | grep -E '^enx'"
ssh -i /config/.ssh/host_key carlo@localhost "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh detect"

# Log router tether check
ssh -i ... root@192.168.0.11 "tail -5 /tmp/android_tether_check.log"

# Stato HA sensors
docker exec homeassistant /config/helpers/usb_tether_ha.sh status server "Debian (192.168.0.3)" 60
```

### Attivazione Modalità da HA (shell_command)
```yaml
shell_command:
  usb_tether_activate: >
    /config/helpers/usb_tether_ha.sh activate server "{{ states('input_select.usb_tether_host') }}" "{{ states('input_number.usb_tether_max_duration') | int(60) }}"
  usb_tether_activate_intranet: >
    /config/helpers/usb_tether_ha.sh activate intranet "{{ states('input_select.usb_tether_host') }}" "{{ states('input_number.usb_tether_max_duration') | int(60) }}"
  usb_tether_restore: >
    /config/helpers/usb_tether_ha.sh restore server "{{ states('input_select.usb_tether_host') }}" "{{ states('input_number.usb_tether_max_duration') | int(60) }}"
  check_android_tether: >
    ssh -i /config/.ssh/router_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o LogLevel=ERROR root@192.168.0.11 "/usr/bin/check_and_restore_android_tether.sh"
```

---

## ⚠️ Pitfalls Noti e Workaround

### 1. MIUI USB Function Switching Bug
- `svc usb setFunctions rndis,adb` crasha: `FileNotFoundException: theme_compatibility.xml`
- `setprop sys.usb.config rndis,adb` → "Failed to set property" (read-only)
- **Workaround**: Attivare tethering USB **manualmente** sul telefono (Settings → Developer Options → USB Configuration → "USB tethering")

### 2. ADB Key Persistence (Router Scripts)
- Hotplug scripts hanno `$HOME` diverso → ADB genera nuova chiave RSA ogni volta → re-authorization
- **Fix**: `export HOME=/root` **prima** di ogni chiamata `adb_router` in `/etc/hotplug.d/usb/99-usb-tethering` e `enable_usb_tether.sh`

### 3. WiFi Calling Loop Routing (Note 11 su router)
- Se WiFi del Note 11 attivo su LAN di casa → Android preferisce WiFi per dati tethering → loop: router → WiFi → telefono → tethering USB → router
- **Soluzione**: **Disattivare "Usa WiFi per le chiamate" (WiFi Calling) dall'UI del telefono**. `settings put global wifi_calling_enabled 0` via ADB viene ribaltato dall'UI.

### 4. Subnet RNDIS Variabile
- IP telefono/router USB cambiano a ogni riconnessione (DHCP telefono)
- Script usano rilevamento dinamico (`ip -br addr show dev usb0`), **mai IP hardcoded**
- StreamPack: alias IP `.10` calcolato da subnet corrente

### 5. JFFS2 Overlay Saturation (Router)
- Se `/overlay` < 500KB liberi → scritture falliscono silenziosamente (read-only)
- Verifica: `df -h /overlay`
- Pulizia: controllare `/overlay/upper/` per residui build/pacchetti

### 6. Command_Line Sensor Scheduling (HA 2026.9)
- `scan_interval` ignorato per comandi SSH
- **Workaround**: Automazione periodica aggiorna `input_text` direttamente; template sensors leggono `input_text`

---

## 📱 StreamPack RTMP over USB Tethering

**Architettura:**
```
Redmi Note 11 (rndis0) → Router usb0 → Alias IP .10 su Debian (192.168.0.3) → MediaMTX :1935 → Frigate
```

**Componenti:**
- **Router**: `streampack-rndis-configure.sh` (hotplug) → Proxy ARP + nftables SNAT/DNAT + scrive config in internal storage app via `run-as`
- **Debian**: `host_scripts/usb_tether.sh` → `enable_nat_router` + `setup_alias` (assegna alias `.10/32` su `enp2s0`)
- **MediaMTX**: Docker `network_mode: host`, ascolta `*:1935` (risponde anche su alias)
- **StreamPack URL**: `rtmp://<alias>.10:1935/live/telefono` (MAI IP fisso storico)

---

## 🔗 Riferimenti Incrociati

| Documento | Contenuto |
|-----------|-----------|
| `RETE_LOCALE.md` | Architettura rete, routing, modalità, WiFi Calling fix |
| `ANDROID_NOTE11_ROUTER_USB_TETHERING_ANALYSIS.md` | Analisi dispositivi, IP Webcam, scrcpy, ADB TCP 5555 |
| `TELECAMERE.md` | NVR, Frigate, Agent DVR, smartphone come IP Camera |
| `ADB_TCPIP_5555_SUCCESS.md` | ADB wireless via `adb tcpip 5555` (funzionante) |
| `ADB_WIRELESS_ATTEMPT.md` | Tentativo fallito `settings put` wireless debugging |
| `OTTIMIZZAZIONE_TELEFONO.md` | Ottimizzazioni ADB Redmi Note 13 Pro 5G / Xiaomi 17 Ultra |
| `usb-tethering-preflight-check.md` (skills) | Error Marker Pattern, ADB key persistence |

---

## ✅ Checklist Stato Attuale (Ottobre 2026)

### Router (Note 11 Pro 5G / `veux`)
- [x] ADB autorizzato (`69a47f6d3a61 device`)
- [x] USB Tethering RNDIS attivo (`sys.usb.config = rndis,none,adb`)
- [x] `usb0` UP con IP `10.203.33.x/24`
- [x] Default route `usb0 metric 10` (in Normale)
- [x] `check_and_restore_android_tether.sh` deployato e testato
- [x] Systemd timer Debian chiama check ogni 5 min
- [x] WiFi Calling **OFF** su UI telefono (evita loop routing)
- [x] ADB TCP 5555 attivo per scrcpy (riattivato da `router_wan_up`)
- [x] StreamPack RTMP funzionante via alias dinamico

### Debian (Xiaomi 17 Ultra)
- [x] Interfaccia `enx663bd50a4461` rilevata con IP `10.157.77.37`
- [x] Gateway `10.157.77.9` raggiungibile
- [x] `tether_check.sh` aggiornato: detection generica (non solo `enx*`)
- [x] `tether_status.json` include sezione `debian` con stato OK
- [x] Template sensor `sensor.internet_android_debian` mostra "OK"
- [x] Dashboard mostra stato corretto

### Home Assistant
- [x] Package `usb_tether.yaml` caricato senza conflitti `script:`
- [x] Scripts in `yaml_generator/scripts/scripts.yaml` (dict merge)
- [x] Template sensors in `yaml_generator/managed_sensors/usb_tether_internet.yaml`
- [x] Automazione periodica 5min funzionale (aggiorna input_text)
- [x] Startup automation `homeassistant_started` + update_entity
- [x] Dashboard "Tethering USB" + "Status Apparati" operativi
- [x] HACS disabilitato temporaneamente (startup block 4597 repos)

---

## 📝 Note per Sviluppi Futuri

1. **Fail-open Normale → Intranet**: Se in Normale il Note 11 non è sul router, la LAN resta isolata. Implementare failover automatico verso Debian su richiesta.

2. **Monitoraggio bearer LTE**: Aggiungere check `mobile_data` + `svc data enable` in automazione periodica per prevenire WAN morta.

3. **Unificazione detection interfacce**: Estendere `detect` in `usb_tether.sh` Debian per supportare anche `rndis0`, `usb0` oltre a `enx*` (già fatto in `tether_check.sh`).

4. **Dashboard real-time**: Valutare WebSocket per aggiornamento istantaneo stati invece di poll 60s.

5. **Documentazione viva**: Questo file è la **singola fonte di verità** per il tethering. Aggiornare qui ogni cambiamento significativo.

---

*Ultimo aggiornamento: 2026-10-19 — Consolidamento da ANDROID_NOTE11_ROUTER_USB_TETHERING_ANALYSIS.md, RETE_LOCALE.md, TELECAMERE.md, usb-tethering-preflight-check.md, ADB_TCPIP_5555_SUCCESS.md, OTTIMIZZAZIONE_TELEFONO.md, e stato runtime verificato.*