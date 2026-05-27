import asyncio
import sys
import logging
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

logging.basicConfig(level=logging.DEBUG)

# List of devices to test
devices = [
    {'addr': '192.168.0.18', 'id': 'bf0e2041fb7f7875c4bcss', 'key': 'rxK|P`^b6]q2Edcf', 'ver': 3.4},
    {'addr': '192.168.0.36', 'id': 'bfbce6d494de7a397dtvjz', 'key': "gh8r[SJJuY]M'uZ$", 'ver': 3.4}
]

async def test_session(device):
    print(f"Testing device {device['id']}...")
    try:
        # Attempt connection multiple times to see if it's intermittent
        for i in range(3):
            print(f"Attempt {i+1}")
            p = await connect(address=device['addr'], device_id=device['id'], local_key=device['key'],
                              protocol_version=device['ver'], enable_debug=True, timeout=10)
            await p.detect_available_dps()
            print(f"Success on attempt {i+1}")
            p.transport.close()
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error for {device['id']}: {e}")

async def main():
    for d in devices:
        await test_session(d)

asyncio.run(main())
