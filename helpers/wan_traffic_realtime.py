import json
import subprocess
import time
import os

ROUTER_IP = "192.168.0.11"
# Path handling for both HA and local testing
CONFIG_DIR = "/config" if os.path.exists("/config") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_KEY = os.path.join(CONFIG_DIR, ".ssh/router_key")
CACHE_FILE = os.path.join(CONFIG_DIR, "temp/wan_traffic_realtime.json") if os.path.exists("/config") else os.path.join(os.path.dirname(CONFIG_DIR), "temp/wan_traffic_realtime.json")
SSH_TIMEOUT = 6


def empty_result(error=None):
    """Return a valid JSON result even when router polling fails."""
    result = {
        "rx_kbps": 0,
        "tx_kbps": 0,
        "rx_bytes": 0,
        "tx_bytes": 0,
        "time": time.time(),
    }
    if error:
        result["error"] = error
    return result


def load_cached_result(error=None):
    """Load last known values, but reset rates to zero for stale samples."""
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)
        return {
            "rx_kbps": 0,
            "tx_kbps": 0,
            "rx_bytes": int(cached.get("rx_bytes", 0)),
            "tx_bytes": int(cached.get("tx_bytes", 0)),
            "time": time.time(),
            "stale": True,
            "error": error or cached.get("error", "stale data"),
        }
    except Exception:
        return empty_result(error)


def run_router_command(remote_command):
    """Run a bounded SSH command against the router."""
    cmd = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "BatchMode=yes",
        "-o", "ControlMaster=auto",
        "-o", f"ControlPath={CONFIG_DIR}/temp/ssh_mux_%h_%p_%r",
        "-o", "ControlPersist=60s",
        "-o", f"ConnectTimeout={SSH_TIMEOUT}",
        "-o", "ServerAliveInterval=2",
        "-o", "ServerAliveCountMax=1",
        "root@" + ROUTER_IP,
        remote_command,
    ]

    return subprocess.check_output(
        cmd,
        stderr=subprocess.DEVNULL,
        timeout=SSH_TIMEOUT + 2,
    ).decode("utf-8").strip()


def fetch_raw_bytes():
    """Fetch WAN byte counters from the router with one SSH round trip."""
    remote_command = r"""
for iface in usb0 wan eth0 pppoe-wan; do
  [ -e "/sys/class/net/$iface" ] || continue
  carrier="$(cat "/sys/class/net/$iface/carrier" 2>/dev/null || echo 1)"
  [ "$carrier" = "1" ] || continue
  if ip -4 addr show dev "$iface" 2>/dev/null | grep -q 'inet '; then
    awk -v iface="$iface" '$1 ~ iface":" {print iface, $2, $10; exit}' /proc/net/dev
    exit
  fi
done
awk '$1 ~ "usb0:" {print "usb0", $2, $10; exit}' /proc/net/dev
"""
    try:
        output = run_router_command(remote_command)
    except Exception as e:
        import sys
        sys.stderr.write(f"[wan_traffic] Error fetching data: {e}\n")
        return None, None

    parts = output.split()
    if len(parts) < 3:
        return None, None

    try:
        rx_bytes = int(parts[1])
        tx_bytes = int(parts[2])
        return rx_bytes, tx_bytes
    except ValueError:
        return None, None


def main():
    current_time = time.time()
    rx, tx = fetch_raw_bytes()

    if rx is None:
        print(json.dumps(load_cached_result("Failed to fetch data")))
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

    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(result, f)
    except Exception:
        pass


if __name__ == "__main__":
    main()
