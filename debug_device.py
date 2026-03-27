import sys
import asyncio
import logging
import json

# Add localtuya/core to path
sys.path.append("/config/custom_components/localtuya/core")
from pytuya import connect, TuyaListener

logging.basicConfig(level=logging.DEBUG)

async def debug():
    dev_config = {
        'host': '192.168.0.36',
        'device_id': 'bfbce6d494de7a397dtvjz',
        'local_key': "gh8r[SJJuY]M'uZ$",
        'protocol_version': 3.4
    }
    
    print(f"DEBUG: Attempting connection to {dev_config['host']}...")
    
    class SimpleListener(TuyaListener):
        def status_updated(self, status): print(f"DEBUG: Status Update: {status}")
        def disconnected(self, exc=""): print(f"DEBUG: Disconnected: {exc}")
        def subdevice_state_updated(self, state): print(f"DEBUG: Subdevice state: {state}")

    try:
        protocol = await asyncio.wait_for(connect(
            address=dev_config['host'],
            device_id=dev_config['device_id'],
            local_key=dev_config['local_key'],
            protocol_version=dev_config['protocol_version'],
            enable_debug=True,
            listener=lambda: SimpleListener(),
            timeout=10
        ), timeout=12)
        
        print("DEBUG: Connection success! Handshake should be done.")
        print("DEBUG: Sending status request...")
        await protocol.status()
        
        await asyncio.sleep(5)
        protocol.transport.close()
    except Exception as e:
        print(f"DEBUG: Failed with error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(debug())
