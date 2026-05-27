import asyncio
import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

async def test():
    try:
        # Re-testing the one from the API call logs that failed
        # The failed device ID in logs was: bf0e2041fb7f7875c4bcss
        # The device name in the list was: stox fancoil sala
        # The device IP is 192.168.0.18
        # The local key in the list is: GTe:*bYzQ3-62-Bz
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key='GTe:*bYzQ3-62-Bz',
                          protocol_version=3.4, enable_debug=True, timeout=10)
        print("Connected!")
        res = await p.detect_available_dps()
        print("DPS:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
