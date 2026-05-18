import asyncio
import sys
import logging
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

logging.basicConfig(level=logging.DEBUG)

async def test():
    try:
        # Increased timeout to see if it makes a difference
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key='rxK|P`^b6]q2Edcf',
                          protocol_version=3.4, enable_debug=True, timeout=20)
        print("Connected!")
        await p.detect_available_dps()
        print("DPS detection successful")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
