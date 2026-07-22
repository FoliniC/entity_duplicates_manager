import json
import subprocess
import time
import os
import socket

ROUTER_IP = "192.168.0.11"
# Robust path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_KEY = os.path.join(BASE_DIR, ".ssh/router_key")
CACHE_FILE = os.path.join(BASE_DIR, "temp/router_traffic_cache.json")

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
        json_start = raw_output.find("{")
        json_end = raw_output.rfind("}")
        if json_start == -1 or json_end == -1 or json_end < json_start:
            raise ValueError("Router command did not return JSON")
        return json.loads(raw_output[json_start:json_end + 1])
    except Exception as e:
        return {"error": str(e)}

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

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except:
        pass # Silently fail if cannot write cache (e.g. permission issues in some envs)

def main():
    current_time = time.time()
    stats = fetch_stats()
    if "error" in stats:
        print(json.dumps(stats))
        return

    cache = load_cache()
    last_stats_data = cache.get("last_data", [])
    last_time = cache.get("last_time", current_time - 60)
    name_cache = cache.get("name_cache", {})
    
    time_delta = current_time - last_time
    if time_delta <= 0: time_delta = 1

    cols = stats.get("columns", [])
    try:
        idx_mac = cols.index("mac")
        idx_ip = cols.index("ip")
        idx_rx = cols.index("rx_bytes")
        idx_tx = cols.index("tx_bytes")
    except ValueError:
        print(json.dumps({"error": "Invalid columns from router"}))
        return

    current_map = {}
    for item in stats.get("data", []):
        ip = item[idx_ip]
        if ip:
            current_map[ip] = {"rx": item[idx_rx], "tx": item[idx_tx], "mac": item[idx_mac]}

    last_map = {}
    if last_stats_data:
        for item in last_stats_data:
            if len(item) > idx_ip:
                ip = item[idx_ip]
                last_map[ip] = {"rx": item[idx_rx], "tx": item[idx_tx]}

    processed = []
    for ip, data in current_map.items():
        last = last_map.get(ip, {"rx": data["rx"], "tx": data["tx"]})
        
        rx_delta = data["rx"] - last["rx"] if data["rx"] >= last["rx"] else data["rx"]
        tx_delta = data["tx"] - last["tx"] if data["tx"] >= last["tx"] else data["tx"]
        
        rx_speed = (rx_delta * 8) / (time_delta * 1024) # kbps
        tx_speed = (tx_delta * 8) / (time_delta * 1024) # kbps
        
        processed.append({
            "ip": ip,
            "name": get_hostname(ip, name_cache),
            "total_rx_mb": round(data["rx"] / (1024*1024), 2),
            "total_tx_mb": round(data["tx"] / (1024*1024), 2),
            "rx_kbps": round(rx_speed, 2),
            "tx_kbps": round(tx_speed, 2)
        })

    processed.sort(key=lambda x: x["total_rx_mb"], reverse=True)

    output = {
        "top_consumers": processed[:50], # Increase to top 50
        "total_rx_gb": round(sum(d["rx"] for d in current_map.values()) / (1024**3), 3),
        "total_tx_gb": round(sum(d["tx"] for d in current_map.values()) / (1024**3), 3),
        "timestamp": current_time
    }

    print(json.dumps(output))

    cache["last_data"] = stats.get("data", [])
    cache["last_time"] = current_time
    cache["name_cache"] = name_cache
    save_cache(cache)

if __name__ == "__main__":
    main()
