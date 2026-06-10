import json
import subprocess
import time
import os

ROUTER_IP = "192.168.0.11"
# Path handling for both HA and local testing
CONFIG_DIR = "/config" if os.path.exists("/config") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH_KEY = os.path.join(CONFIG_DIR, ".ssh/router_key")
CACHE_FILE = os.path.join(CONFIG_DIR, "temp/wan_traffic_realtime.json")
INTERFACE = "usb0"

def fetch_raw_bytes():
    cmd = [
        "ssh", 
        "-i", SSH_KEY, 
        "-o", "StrictHostKeyChecking=no", 
        "-o", "UserKnownHostsFile=/dev/null", 
        "root@" + ROUTER_IP, 
        f"grep {INTERFACE} /proc/net/dev"
    ]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8').strip()
        # format: usb0: RX_BYTES RX_PACKETS ... TX_BYTES TX_PACKETS ...
        # parts[0] is 'usb0:'
        parts = output.split()
        rx_bytes = int(parts[1])
        tx_bytes = int(parts[9])
        return rx_bytes, tx_bytes
    except Exception as e:
        return None, None

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
        except:
            prev = {"rx_bytes": rx, "tx_bytes": tx, "time": current_time - 1}
    else:
        prev = {"rx_bytes": rx, "tx_bytes": tx, "time": current_time - 1}

    delta_time = current_time - prev.get("time", current_time - 1)
    if delta_time <= 0: delta_time = 0.1
    
    rx_speed = (rx - prev.get("rx_bytes", rx)) * 8 / (delta_time * 1024) # kbps
    tx_speed = (tx - prev.get("tx_bytes", tx)) * 8 / (delta_time * 1024) # kbps
    
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
