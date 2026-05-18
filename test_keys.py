import asyncio
import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

async def test_key(key):
    try:
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key=key,
                          protocol_version=3.4, enable_debug=True, timeout=5)
        await p.detect_available_dps()
        print(f"Key success")
        return True
    except Exception as e:
        print(f"Key failed: {e}")
        return False

async def main():
    keys = ['rxK|P`^b6]q2Edcf', 'GTe:*bYzQ3-62-Bz', 'HTV}N2)7)Rl3!\'v<']
    for k in keys:
        print(f"Testing {k}")
        await test_key(k)

asyncio.run(main())
