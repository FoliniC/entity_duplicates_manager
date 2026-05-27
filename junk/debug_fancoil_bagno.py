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
        'host': '192.168.0.13',
        'device_id': 'bfe87aa348c2ffc93abqaq',
        'local_key': "]WR4TKn7!`X2k(_<",
        'protocol_version': 3.4
    }
    
    print(f"DEBUG: Attempting connection to {dev_config['host']}...")
    
    class SimpleListener(TuyaListener):
        def status_updated(self, status): print(f"DEBUG: Status Update: {status}")
        def disconnected(self, exc=""): print(f"DEBUG: Disconnected: {exc}")
        def subdevice_state_updated(self, state): print(f"DEBUG: Subdevice state: {state}")

    p = None
    try:
        p = await asyncio.wait_for(connect(
            address=dev_config['host'],
            device_id=dev_config['device_id'],
            local_key=dev_config['local_key'],
            protocol_version=dev_config['protocol_version'],
            enable_debug=True,
            listener=lambda: SimpleListener(),
            timeout=10
        ), timeout=12)
        
        print("DEBUG: Connection success! Handshake done.")
        print("DEBUG: Current Status...")
        res = await p.detect_available_dps()
        print(f"DEBUG: Current DPs: {res}")
        
        # Test switch command on DP 1 (usually first switch)
        # We try to toggle whatever it is.
        target_val = not res.get('1', False)
        print(f"DEBUG: Attempting to set DP 1 to {target_val}...")
        await p.set_dps({'1': target_val})
        
        await asyncio.sleep(2)
        print("DEBUG: Verification Status...")
        res_after = await p.detect_available_dps()
        print(f"DEBUG: DPs after command: {res_after}")

    except Exception as e:
        print(f"DEBUG: Failed with error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if p and p.transport: p.transport.close()

if __name__ == "__main__":
    asyncio.run(debug())
