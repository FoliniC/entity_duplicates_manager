import asyncio
import logging
import sys

sys.path.append("/config/custom_components/localtuya/core")
from pytuya import connect, TuyaListener

logging.basicConfig(level=logging.DEBUG)

async def test():
    # Fancoil bagno
    cfg = {
        'host': '192.168.0.13',
        'id': 'bfe87aa348c2ffc93abqaq',
        'key': ']WR4TKn7!`X2k(_<',
        'ver': 3.4
    }
    
    print(f"Connecting to {cfg['host']}...")
    
    class L(TuyaListener):
        def status_updated(self, s): print(f"Update: {s}")
        def disconnected(self, e=""): print(f"Disc: {e}")
        def subdevice_state_updated(self, s): pass

    try:
        p = await asyncio.wait_for(connect(
            address=cfg['host'], device_id=cfg['id'], local_key=cfg['key'],
            protocol_version=cfg['ver'], enable_debug=True, listener=lambda: L(), timeout=10
        ), timeout=12)
        
        print("Connected! Handshake done.")
        
        print("1. Testing standard status()...")
        try:
            s = await asyncio.wait_for(p.status(), timeout=5)
            print(f"Status Result: {s}")
        except Exception as e:
            print(f"Status Failed: {e}")

        print("2. Testing detect_available_dps()...")
        try:
            d = await asyncio.wait_for(p.detect_available_dps(), timeout=5)
            print(f"Probe Result: {d}")
        except Exception as e:
            print(f"Probe Failed: {e}")

        await asyncio.sleep(2)
        p.transport.close()
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
