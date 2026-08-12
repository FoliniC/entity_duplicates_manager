import json
import subprocess
import time
import os
import re

ROUTER_IP = "192.168.0.11"
# Path handling for both HA and local testing
CONFIG_DIR = "/config" if os.path.exists("/config") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_KEY = os.path.join(CONFIG_DIR, ".ssh/router_key")
CACHE_FILE = os.path.join(CONFIG_DIR, "temp/wan_traffic_realtime.json") if os.path.exists("/config") else os.path.join(os.path.dirname(CONFIG_DIR), "temp/wan_traffic_realtime.json")


def get_active_interface():
    """Rileva l'interfaccia attiva controllando /proc/net/dev e le proprietà carrier/IP."""
    cmd = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", f"ControlPath={CONFIG_DIR}/temp/ssh_mux_%h_%p_%r",
        "-o", "ControlPersist=60s",
        "root@" + ROUTER_IP,
        "ip -br link 2>/dev/null"
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8')
    except Exception:
        return "usb0"  # fallback

    # Pattern per escludere interfacce virtuali/non-rilevanti
    exclude_patterns = [
        r'^lo$',                           # loopback
        r'^docker[0-9]*$',                 # docker veth
        r'^br-.*$',                        # bridges (br-lan, br-*)
        r'^veth[a-f0-9]+(@.*)?$',         # veth pairs
        r'^zt[a-z0-9]+$',                  # wireguard
        r'^tun[0-9]*$',                    # tuns
        r'^wlan[0-9]+$',                   # wireless interfaces
        # NON escludere usb* - sono interfacce WAN/tethering
    ]

    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            iface = parts[0]
            # Verifica se l'interfaccia corrisponde a un pattern di esclusione
            skip = False
            for pattern in exclude_patterns:
                if re.match(pattern, iface):
                    skip = True
                    break
            if skip:
                continue

            # Controlla carrier (must be 1 = up)
            try:
                intf_cmd = [
                    "ssh", "-i", SSH_KEY,
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-o", f"ControlPath={CONFIG_DIR}/temp/ssh_mux_%h_%p_%r",
                    "-o", "ControlPersist=60s",
                    "root@" + ROUTER_IP,
                    f"cat /sys/class/net/{iface}/carrier 2>/dev/null"
                ]
                carrier_output = subprocess.check_output(intf_cmd, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                if carrier_output != "1":
                    continue
            except Exception:
                continue

            # Controlla IPv4 address
            try:
                ip_cmd = [
                    "ssh", "-i", SSH_KEY,
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    "-o", f"ControlPath={CONFIG_DIR}/temp/ssh_mux_%h_%p_%r",
                    "-o", "ControlPersist=60s",
                    "root@" + ROUTER_IP,
                    f"ip -4 addr show dev {iface} 2>/dev/null"
                ]
                ip_output = subprocess.check_output(ip_cmd, stderr=subprocess.DEVNULL).decode('utf-8')
                if 'inet ' in ip_output:
                    return iface
            except Exception:
                pass

    return "usb0"  # fallback


def fetch_raw_bytes():
    # Use SSH Multiplexing to keep the session alive and reduce overhead
    INTERFACE = get_active_interface()
    # DEBUG: log the detected interface
    import sys
    sys.stderr.write(f"[wan_traffic] Detected interface: {INTERFACE}\n")

    cmd = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", f"ControlPath={CONFIG_DIR}/temp/ssh_mux_%h_%p_%r",
        "-o", "ControlPersist=60s",
        "root@" + ROUTER_IP,
        f"grep {INTERFACE} /proc/net/dev"
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8').strip()
    except Exception as e:
        import sys
        sys.stderr.write(f"[wan_traffic] Error fetching data: {e}\\n")
        return None, None

    # format: usb0: RX_BYTES RX_PACKETS ... TX_BYTES TX_PACKETS ...
    # parts[0] is 'usb0:'
    parts = output.split()
    if len(parts) < 10:
        return None, None

    rx_bytes = int(parts[1])
    tx_bytes = int(parts[9])
    return rx_bytes, tx_bytes


def main():
    current_time = time.time()
    rx, tx = fetch_raw_bytes()

    if rx is None:
        print(json.dumps({"error": "Failed to fetch data"}))
        return

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                prev = json.load(f)
        except Exception:
            prev = {"rx_bytes": rx, "tx_bytes": tx, "time": current_time - 1}
    else:
        prev = {"rx_bytes": rx, "tx_bytes": tx, "time": current_time - 1}

    delta_time = current_time - prev.get("time", current_time - 1)
    if delta_time <= 0: delta_time = 0.1

    rx_speed = (rx - prev.get("rx_bytes", rx)) * 8 / (delta_time * 1024)  # kbps
    tx_speed = (tx - prev.get("tx_bytes", tx)) * 8 / (delta_time * 1024)  # kbps

    # Handle wrap around or reset
    if rx_speed < 0: rx_speed = 0
    if tx_speed < 0: tx_speed = 0

    result = {
        "rx_kbps": round(rx_speed, 2),
        "tx_kbps": round(tx_speed, 2),
        "rx_bytes": rx,
        "tx_bytes": tx,
        "time": current_time
    }

    print(json.dumps(result))

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()