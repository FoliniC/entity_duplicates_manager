import asyncio
import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

async def test():
    try:
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key='rxK|P`^b6]q2Edcf',
                          protocol_version=3.4, enable_debug=True, timeout=10)
        print("Connected!")
        res = await p.detect_available_dps()
        print("DPS:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
