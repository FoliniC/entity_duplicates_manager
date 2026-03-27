import sys
import os
import asyncio
import logging
import json
import traceback

# Add custom components to path
# We append localtuya/core so we can import pytuya directly
sys.path.append("/config/custom_components/localtuya/core")

try:
    from pytuya import connect, TuyaListener, SubdeviceState
except ImportError as e:
    print(f"Failed to import localtuya: {e}")
    print("sys.path:", sys.path)
    sys.exit(1)

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class MyListener(TuyaListener):
    def __init__(self):
        self.sub_devices = {}

    def status_updated(self, status):
        print(f"\n--- STATUS UPDATED ---\n{json.dumps(status, indent=2)}\n----------------------\n")

    def disconnected(self, exc=""):
        print(f"\n--- DISCONNECTED: {exc} ---\n")

    def subdevice_state_updated(self, state: SubdeviceState):
        print(f"\n--- SUBDEVICE STATE: {state} ---\n")

async def test_device(dev_id, address, local_key, protocol_version, name):
    print(f"\nTesting device: {name} ({dev_id}) at {address} (v{protocol_version})...")
    
    listener = MyListener()
    protocol = None
    try:
        # Use a shorter timeout for connection to detect 'busy' devices faster
        connect_task = asyncio.create_task(connect(
            address=address,
            device_id=dev_id,
            local_key=local_key,
            protocol_version=protocol_version,
            enable_debug=True,
            listener=lambda: listener,
            timeout=5
        ))
        
        protocol = await asyncio.wait_for(connect_task, timeout=7)
        print("TCP Connected! Negotiating session...")
        
        # Wait for session key negotiation (important for 3.4+)
        await asyncio.sleep(1)
        
        print("Requesting status (DP_QUERY)...")
        try:
            status = await asyncio.wait_for(protocol.status(), timeout=5)
            if status:
                print(f"Success! Received status for {name}")
            else:
                print(f"Warning: Connection established but {name} returned empty status. Likely BUSY with another connection (HA).")
        except asyncio.TimeoutError:
            print(f"Timeout: {name} did not respond to status query. Likely BUSY (one-connection limit).")
        
        await asyncio.sleep(1)
    except Exception as e:
        if "Host is unreachable" in str(e):
            print(f"OFFLINE: {name} ({address}) is unreachable.")
        else:
            print(f"Error testing {name}: {e}")
    finally:
        if protocol and protocol.transport:
            print("Closing connection...")
            protocol.transport.close()

async def main():
    print("Reading config entries...")
    config_path = "/config/.storage/core.config_entries"
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        return

    localtuya_entry = None
    for entry in data["data"]["entries"]:
        if entry["domain"] == "localtuya":
            localtuya_entry = entry
            break
    
    if not localtuya_entry:
        print("No localtuya entry found in config.")
        return

    devices = localtuya_entry["data"]["devices"]
    print(f"Found {len(devices)} devices in config.")

    for dev_id, dev_data in devices.items():
        name = dev_data.get("friendly_name", dev_id)
        address = dev_data.get("host")
        local_key = dev_data.get("local_key")
        protocol_version = float(dev_data.get("protocol_version", 3.3))
        
        if not address or not local_key:
            print(f"Skipping {name} (missing host or key)")
            continue
            
        await test_device(dev_id, address, local_key, protocol_version, name)
        # Add a small delay between devices
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
