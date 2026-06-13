import json
import subprocess
import time
import os
import socket
import re

ROUTER_IP = "192.168.0.11"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_KEY = os.path.join(BASE_DIR, ".ssh/router_key")
CACHE_FILE = os.path.join(BASE_DIR, "temp/realtime_per_device.json")

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

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-i", SSH_KEY, 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "UserKnownHostsFile=/dev/null", 
        "-o", "ControlMaster=auto",
        "-o", f"ControlPath={BASE_DIR}/temp/ssh_mux_%h_%p_%r",
        "-o", "ControlPersist=60s",
        "-o", "ConnectTimeout=5",
        f"root@{ROUTER_IP}", cmd
    ]
    try:
        return subprocess.check_output(full_cmd, stderr=subprocess.DEVNULL).decode('utf-8')
    except:
        return ""

def get_active_ips():
    # Get IPs from ARP table to find live devices
    arp_output = run_ssh("cat /proc/net/arp")
    ips = []
    for line in arp_output.splitlines():
        if "0x2" in line: # Complete ARP entry
            parts = line.split()
            if parts:
                ips.append(parts[0])
    return ips

def setup_nft(active_ips):
    # Ensure table and chain exist
    run_ssh("nft add table inet bwmon")
    run_ssh("nft add chain inet bwmon forward '{ type filter hook forward priority 0 ; }'")
    
    # Get current rules to avoid duplicates
    rules = run_ssh("nft list chain inet bwmon forward")
    
    # Add rules for ANY IP we see, not just hardcoded ones
    # Limit to local subnet to avoid explosion
    for ip in active_ips:
        if not ip.startswith("192.168.0."): continue
        
        if f"ip saddr {ip}" not in rules:
            run_ssh(f"nft add rule inet bwmon forward ip saddr {ip} counter")
        if f"ip daddr {ip}" not in rules:
            run_ssh(f"nft add rule inet bwmon forward ip daddr {ip} counter")

def fetch_counters():
    output = run_ssh("nft list chain inet bwmon forward")
    results = {}
    lines = output.splitlines()
    # Rule format: ip saddr 192.168.0.8 counter packets 123 bytes 456
    for line in lines:
        if "counter" in line and "ip" in line:
            parts = line.split()
            try:
                if "saddr" in line:
                    ip = parts[parts.index("saddr")+1]
                    direction = "tx"
                else:
                    ip = parts[parts.index("daddr")+1]
                    direction = "rx"
                
                bytes_idx = parts.index("bytes") + 1
                bytes_val = int(parts[bytes_idx])
                
                if ip not in results:
                    results[ip] = {"rx": 0, "tx": 0}
                results[ip][direction] = bytes_val
            except:
                continue
    return results

def get_hostname(ip, name_cache):
    if ip in MANUAL_NAMES: return MANUAL_NAMES[ip]
    if ip in name_cache: return name_cache[ip]
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        if hostname.endswith(".lan"): hostname = hostname[:-4]
        name_cache[ip] = hostname
        return hostname
    except:
        pass
    name_cache[ip] = ip
    return ip

def main():
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    active_ips = get_active_ips()
    setup_nft(active_ips)
    
    current_time = time.time()
    current_counters = fetch_counters()
    
    if not current_counters:
        print(json.dumps({"error": "No data from router"}))
        return

    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except:
            pass

    last_counters = cache.get("counters", {})
    last_time = cache.get("time", current_time - 15)
    name_cache = cache.get("name_cache", {})
    
    delta_time = current_time - last_time
    if delta_time <= 0: delta_time = 0.1

    processed = []
    for ip, curr in current_counters.items():
        last = last_counters.get(ip, curr)
        
        rx_delta = curr["rx"] - last["rx"] if curr["rx"] >= last["rx"] else curr["rx"]
        tx_delta = curr["tx"] - last["tx"] if curr["tx"] >= last["tx"] else curr["tx"]
        
        rx_speed = (rx_delta * 8) / (delta_time * 1024) # kbps
        tx_speed = (tx_delta * 8) / (delta_time * 1024) # kbps
        
        if rx_speed > 0.5 or tx_speed > 0.5 or ip in MANUAL_NAMES:
            processed.append({
                "ip": ip,
                "name": get_hostname(ip, name_cache),
                "rx_kbps": round(rx_speed, 2),
                "tx_kbps": round(tx_speed, 2)
            })

    processed.sort(key=lambda x: x["rx_kbps"] + x["tx_kbps"], reverse=True)

    result = {
        "devices": processed[:20], # Show top 20 real-time
        "time": current_time,
        "counters": current_counters,
        "name_cache": name_cache
    }
    
    print(json.dumps(result))
    
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(result, f)
    except:
        pass

if __name__ == "__main__":
    main()
