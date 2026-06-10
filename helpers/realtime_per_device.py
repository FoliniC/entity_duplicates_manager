import json
import subprocess
import time
import os

ROUTER_IP = "192.168.0.11"
# Path handling for both HA and local testing
CONFIG_DIR = "/config" if os.path.exists("/config") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_KEY = os.path.join(CONFIG_DIR, ".ssh/router_key")
CACHE_FILE = os.path.join(CONFIG_DIR, "temp/realtime_per_device.json")

DEVICES = {
    "192.168.0.8":  "Desktop",
    "192.168.0.89": "Alexa Camera",
    "192.168.0.90": "Alexa Cucina",
    "192.168.0.3":  "Home Assistant",
}

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-i", SSH_KEY, 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "UserKnownHostsFile=/dev/null", 
        f"root@{ROUTER_IP}", cmd
    ]
    try:
        return subprocess.check_output(full_cmd, stderr=subprocess.DEVNULL).decode('utf-8')
    except:
        return ""

def setup_nft():
    # Ensure table and chain exist
    run_ssh("nft add table inet bwmon")
    run_ssh("nft add chain inet bwmon forward '{ type filter hook forward priority 0 ; }'")
    
    # Check current rules
    rules = run_ssh("nft list chain inet bwmon forward")
    for ip, name in DEVICES.items():
        if f"ip saddr {ip}" not in rules:
            run_ssh(f"nft add rule inet bwmon forward ip saddr {ip} counter")
        if f"ip daddr {ip}" not in rules:
            run_ssh(f"nft add rule inet bwmon forward ip daddr {ip} counter")

def fetch_counters():
    output = run_ssh("nft list chain inet bwmon forward")
    # Rule format: ip saddr 192.168.0.8 counter packets 123 bytes 456
    results = {}
    lines = output.splitlines()
    for line in lines:
        if "counter" in line and "ip" in line:
            parts = line.split()
            try:
                # Find IP and direction
                if "saddr" in line:
                    ip = parts[parts.index("saddr")+1]
                    direction = "tx"
                else:
                    ip = parts[parts.index("daddr")+1]
                    direction = "rx"
                
                # Find bytes
                bytes_val = int(parts[parts.index("bytes")+1])
                
                if ip not in results:
                    results[ip] = {"rx": 0, "tx": 0}
                results[ip][direction] = bytes_val
            except:
                continue
    return results

def main():
    setup_nft()
    current_time = time.time()
    current_counters = fetch_counters()
    
    if not current_counters:
        print(json.dumps({"error": "No data from router"}))
        return

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
    else:
        cache = {}

    last_counters = cache.get("counters", {})
    last_time = cache.get("time", current_time - 15)
    delta_time = current_time - last_time
    if delta_time <= 0: delta_time = 0.1

    processed = []
    for ip, name in DEVICES.items():
        curr = current_counters.get(ip, {"rx": 0, "tx": 0})
        last = last_counters.get(ip, curr)
        
        rx_delta = curr["rx"] - last["rx"] if curr["rx"] >= last["rx"] else curr["rx"]
        tx_delta = curr["tx"] - last["tx"] if curr["tx"] >= last["tx"] else curr["tx"]
        
        rx_speed = (rx_delta * 8) / (delta_time * 1024) # kbps
        tx_speed = (tx_delta * 8) / (delta_time * 1024) # kbps
        
        processed.append({
            "ip": ip,
            "name": name,
            "rx_kbps": round(rx_speed, 2),
            "tx_kbps": round(tx_speed, 2)
        })

    processed.sort(key=lambda x: x["rx_kbps"] + x["tx_kbps"], reverse=True)

    result = {
        "devices": processed,
        "time": current_time,
        "counters": current_counters
    }
    
    print(json.dumps(result))
    
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(result, f)

if __name__ == "__main__":
    main()
