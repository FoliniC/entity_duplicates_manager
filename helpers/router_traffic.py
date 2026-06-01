import json
import subprocess
import time
import os

ROUTER_IP = "192.168.0.11"
SSH_KEY = "/config/.ssh/router_key"
CACHE_FILE = "/config/temp/router_traffic_cache.json"

def fetch_stats():
    cmd = [
        "ssh", 
        "-i", SSH_KEY, 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "UserKnownHostsFile=/dev/null", 
        "root@" + ROUTER_IP, 
        "/usr/libexec/nlbwmon-action download -g mac,ip -o -rx_bytes,-tx_bytes"
    ]
    try:
        raw_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        # Skip potential SSH warnings (lines starting with 'Warning:')
        clean_output = ""
        for line in raw_output.splitlines():
            if not line.startswith("Warning:"):
                clean_output += line
        
        try:
            return json.loads(clean_output)
        except json.JSONDecodeError:
            return {"error": f"JSON decode failed. Raw output: {raw_output}"}
    except Exception as e:
        return {"error": str(e)}

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def main():
    current_time = time.time()
    stats = fetch_stats()
    if "error" in stats:
        print(json.dumps(stats))
        return

    cache = load_cache()
    last_stats = cache.get("last_data", [])
    last_time = cache.get("last_time", current_time - 60)
    
    time_delta = current_time - last_time
    if time_delta <= 0: time_delta = 1

    # Map columns to indices
    cols = stats.get("columns", [])
    idx_mac = cols.index("mac")
    idx_ip = cols.index("ip")
    idx_rx = cols.index("rx_bytes")
    idx_tx = cols.index("tx_bytes")

    # Map mac to stats
    current_map = {}
    for item in stats.get("data", []):
        mac = item[idx_mac]
        if mac:
            current_map[mac] = {"rx": item[idx_rx], "tx": item[idx_tx], "ip": item[idx_ip]}

    last_map = {}
    if last_stats:
        last_cols = cache.get("last_cols", cols)
        try:
            l_idx_mac = last_cols.index("mac")
            l_idx_rx = last_cols.index("rx_bytes")
            l_idx_tx = last_cols.index("tx_bytes")
            for item in last_stats:
                mac = item[l_idx_mac]
                if mac:
                    last_map[mac] = {"rx": item[l_idx_rx], "tx": item[l_idx_tx]}
        except:
            pass

    processed = []
    for mac, data in current_map.items():
        last = last_map.get(mac, {"rx": data["rx"], "tx": data["tx"]})
        
        # Calculate deltas (handle counter reset)
        rx_delta = data["rx"] - last["rx"] if data["rx"] >= last["rx"] else data["rx"]
        tx_delta = data["tx"] - last["tx"] if data["tx"] >= last["tx"] else data["tx"]
        
        rx_speed = (rx_delta * 8) / (time_delta * 1000) # kbps
        tx_speed = (tx_delta * 8) / (time_delta * 1000) # kbps
        
        processed.append({
            "mac": mac,
            "ip": data["ip"],
            "total_rx_mb": round(data["rx"] / (1024*1024), 2),
            "total_tx_mb": round(data["tx"] / (1024*1024), 2),
            "rx_kbps": round(rx_speed, 2),
            "tx_kbps": round(tx_speed, 2)
        })

    # Sort by speed
    processed.sort(key=lambda x: x["rx_kbps"] + x["tx_kbps"], reverse=True)

    output = {
        "top_consumers": processed[:15],
        "total_rx_gb": round(sum(d["rx"] for d in current_map.values()) / (1024*1024*1024), 3),
        "total_tx_gb": round(sum(d["tx"] for d in current_map.values()) / (1024*1024*1024), 3),
        "timestamp": current_time
    }

    print(json.dumps(output))

    # Update cache
    cache["last_data"] = stats.get("data", [])
    cache["last_cols"] = cols
    cache["last_time"] = current_time
    save_cache(cache)

if __name__ == "__main__":
    main()
