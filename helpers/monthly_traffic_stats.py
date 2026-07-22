import json
import subprocess
import time
import os
import socket
from datetime import datetime

ROUTER_IP = "192.168.0.11"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_KEY = os.path.join(BASE_DIR, ".ssh/router_key")
CACHE_FILE = os.path.join(BASE_DIR, "temp/router_traffic_cache.json")
SNAPSHOT_FILE = os.path.join(BASE_DIR, "temp/monthly_traffic_snapshot.json")

MANUAL_NAMES = {
    "192.168.0.3":  "Home Assistant",
    "192.168.0.89": "Alexa Camera",
    "192.168.0.90": "Alexa Cucina",
    "192.168.0.9":  "TCL TV (WiFi)",
    "192.168.0.123": "TCL TV (Alt)",
    "192.168.0.107": "Smart TV (Lan?)",
    "192.168.0.45": "Smart TV Pro",
    "192.168.0.8":   "Desktop PC",
}

def run_ssh(remote_cmd):
    cmd = [
        "ssh", 
        "-i", SSH_KEY, 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=5",
        "root@" + ROUTER_IP, 
        remote_cmd
    ]
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')

def fetch_live_counters():
    setup_cmd = (
        "nft add table inet bwmon 2>/dev/null; "
        "nft add chain inet bwmon forward '{ type filter hook forward priority 0 ; }' 2>/dev/null; "
        "for ip in $(awk '$4==\"0x2\" && $1 ~ /^192\\.168\\.0\\./ {print $1}' /proc/net/arp); do "
        "nft list chain inet bwmon forward 2>/dev/null | grep -q \"ip saddr $ip \" || nft add rule inet bwmon forward ip saddr $ip counter; "
        "nft list chain inet bwmon forward 2>/dev/null | grep -q \"ip daddr $ip \" || nft add rule inet bwmon forward ip daddr $ip counter; "
        "done; "
        "nft list chain inet bwmon forward"
    )
    output = run_ssh(setup_cmd)
    counters = {}
    for line in output.splitlines():
        if "counter" not in line or "ip " not in line:
            continue
        parts = line.split()
        try:
            if "saddr" in parts:
                ip = parts[parts.index("saddr") + 1]
                direction = "tx"
            elif "daddr" in parts:
                ip = parts[parts.index("daddr") + 1]
                direction = "rx"
            else:
                continue
            if not ip.startswith("192.168.0."):
                continue
            bytes_val = int(parts[parts.index("bytes") + 1])
            counters.setdefault(ip, {"rx": 0, "tx": 0, "mac": ""})
            counters[ip][direction] = bytes_val
        except Exception:
            continue

    if not counters:
        raise ValueError("No live nft counters from router")

    return {
        "columns": ["mac", "ip", "rx_bytes", "tx_bytes"],
        "data": [
            [data["mac"], ip, data["rx"], data["tx"]]
            for ip, data in counters.items()
        ],
    }

def fetch_nlbwmon_stats():
    raw_output = run_ssh("/usr/libexec/nlbwmon-action download -g mac,ip -o -rx_bytes,-tx_bytes")
    json_start = raw_output.find("{")
    json_end = raw_output.rfind("}")
    if json_start == -1 or json_end == -1 or json_end < json_start:
        raise ValueError("Router command did not return JSON")
    return json.loads(raw_output[json_start:json_end + 1])

def fetch_stats():
    try:
        return fetch_live_counters()
    except Exception as e:
        try:
            return fetch_nlbwmon_stats()
        except Exception as fallback_error:
            return {"error": f"{e}; fallback failed: {fallback_error}"}

def get_hostname(ip, name_cache):
    if ip in MANUAL_NAMES:
        return MANUAL_NAMES[ip]
    if ip in name_cache:
        return name_cache[ip]
    
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if hostname.endswith(".lan"):
            hostname = hostname[:-4]
        name_cache[ip] = hostname
        return hostname
    except:
        pass
    
    name_cache[ip] = ip
    return ip

def load_snapshot():
    """Load the monthly snapshot for period tracking."""
    if os.path.exists(SNAPSHOT_FILE):
        try:
            with open(SNAPSHOT_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return None

def save_snapshot(snapshot):
    """Save the monthly snapshot."""
    try:
        os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
        with open(SNAPSHOT_FILE, 'w') as f:
            json.dump(snapshot, f)
    except:
        pass

def should_reset_snapshot(start_day):
    """Check if we need to reset snapshot (new period started)."""
    if not os.path.exists(SNAPSHOT_FILE):
        return True
    
    try:
        stat = os.stat(SNAPSHOT_FILE)
        snapshot_time = datetime.fromtimestamp(stat.st_mtime)
        now = datetime.now()
        
        # Reset if we've passed the start_day in a new month
        if now.month != snapshot_time.month:
            if now.day >= start_day:
                return True
            else:
                return False
        # If same month but snapshot is from before start_day and we're past it
        if snapshot_time.day < start_day and now.day >= start_day:
            return True
        return False
    except:
        return True

def main():
    current_time = time.time()
    stats = fetch_stats()
    if "error" in stats:
        print(json.dumps({"error": stats["error"], "period_total_mb": 0, "period_by_device": []}))
        return

    # Load start day from input_number (default 23)
    start_day_input = 23
    input_file = os.path.join(BASE_DIR, "temp/usage_start_day.txt")
    if os.path.exists(input_file):
        try:
            with open(input_file, 'r') as f:
                start_day_input = int(f.read().strip())
        except:
            pass

    cols = stats.get("columns", [])
    try:
        idx_mac = cols.index("mac")
        idx_ip = cols.index("ip")
        idx_rx = cols.index("rx_bytes")
        idx_tx = cols.index("tx_bytes")
    except ValueError:
        print(json.dumps({"error": "Invalid columns from router", "period_total_mb": 0, "period_by_device": []}))
        return

    # Build current traffic map
    current_map = {}
    for item in stats.get("data", []):
        ip = item[idx_ip]
        if ip:
            current_map[ip] = {"rx": item[idx_rx], "tx": item[idx_tx], "mac": item[idx_mac]}

    # Calculate period totals
    snapshot = load_snapshot()
    period_start = None
    
    if snapshot is None or should_reset_snapshot(start_day_input):
        # Take new snapshot for period start
        now = datetime.now()
        snapshot = {
            "start_time": current_time,
            "start_date": now.strftime("%Y-%m-%d"),
            "device_snapshots": {}
        }
        # Save current values as baseline (they'll be subtracted)
        for ip, data in current_map.items():
            snapshot["device_snapshots"][ip] = {"rx": data["rx"], "tx": data["tx"]}
        save_snapshot(snapshot)
        period_start = snapshot["start_date"]
    else:
        # Calculate differences from snapshot
        period_start = snapshot.get("start_date", "N/A")
        for ip, data in current_map.items():
            if ip not in snapshot.get("device_snapshots", {}):
                snapshot["device_snapshots"][ip] = {"rx": 0, "tx": 0}

    # Calculate period usage (MB)
    period_total_bytes = 0
    period_by_device = []
    name_cache = {}
    
    for ip, data in current_map.items():
        snap = snapshot["device_snapshots"].get(ip, {"rx": 0, "tx": 0})
        
        # Handle counter resets (when device reconnects)
        rx_diff = data["rx"] - snap["rx"] if data["rx"] >= snap["rx"] else data["rx"]
        tx_diff = data["tx"] - snap["tx"] if data["tx"] >= snap["tx"] else data["tx"]
        
        if rx_diff > 0 or tx_diff > 0:
            period_by_device.append({
                "ip": ip,
                "name": get_hostname(ip, name_cache),
                "period_rx_mb": round(rx_diff / (1024 * 1024), 2),
                "period_tx_mb": round(tx_diff / (1024 * 1024), 2)
            })
            period_total_bytes += rx_diff

    period_by_device.sort(key=lambda x: x["period_rx_mb"], reverse=True)

    output = {
        "period_total_mb": round(period_total_bytes / (1024 * 1024), 2),
        "period_by_device": period_by_device[:10],
        "period_start_date": period_start,
        "current_time": current_time
    }

    print(json.dumps(output))

if __name__ == "__main__":
    main()
