import asyncio
import sys
import logging
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

logging.basicConfig(level=logging.DEBUG)

async def test_device(addr, dev_id, key, ver):
    print(f"Testing device {dev_id} ({addr}) ver {ver}")
    try:
        p = await connect(address=addr, device_id=dev_id, local_key=key,
                          protocol_version=ver, enable_debug=True, timeout=10)
        await p.detect_available_dps()
        print(f"Success for {dev_id}!")
    except Exception as e:
        print(f"Failed {dev_id}: {e}")

async def main():
    # Devices list from the earlier API call
    devices = [
        {'addr': '192.168.0.18', 'id': 'bf0e2041fb7f7875c4bcss', 'key': 'rxK|P`^b6]q2Edcf', 'ver': 3.4},
        {'addr': '192.168.0.36', 'id': 'bfbce6d494de7a397dtvjz', 'key': "gh8r[SJJuY]M'uZ$", 'ver': 3.4}
    ]
    for d in devices:
        await test_device(d['addr'], d['id'], d['key'], d['ver'])

asyncio.run(main())
