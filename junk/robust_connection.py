import asyncio
import sys
import logging
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

logging.basicConfig(level=logging.DEBUG)

async def robust_connect(address, device_id, local_key, protocol_version, retries=5):
    for i in range(retries):
        try:
            print(f"Connection attempt {i+1} for {device_id}...")
            p = await connect(address=address, device_id=device_id, local_key=local_key,
                              protocol_version=protocol_version, enable_debug=True, timeout=10)
            print("Connected successfully!")
            return p
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            await asyncio.sleep(2)
    raise Exception(f"Failed to connect after {retries} attempts")

async def test():
    try:
        p = await robust_connect('192.168.0.18', 'bf0e2041fb7f7875c4bcss', 'rxK|P`^b6]q2Edcf', 3.4)
        await p.detect_available_dps()
        print("Final success!")
        p.transport.close()
    except Exception as e:
        print(f"Final error: {e}")

asyncio.run(test())
