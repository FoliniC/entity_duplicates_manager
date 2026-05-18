import asyncio
import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

async def test():
    # Trying with the original one again, just to be sure it actually works.
    try:
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key='rxK|P`^b6]q2Edcf',
                          protocol_version=3.4, enable_debug=True, timeout=10)
        print("Test 1 (original key) Connected!")
    except Exception as e:
        print("Test 1 Error:", e)
        
    try:
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key='GTe:*bYzQ3-62-Bz',
                          protocol_version=3.4, enable_debug=True, timeout=10)
        print("Test 2 (list key) Connected!")
    except Exception as e:
        print("Test 2 Error:", e)

asyncio.run(test())
