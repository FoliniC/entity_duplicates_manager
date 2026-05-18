import asyncio
import sys
import logging
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect

logging.getLogger('pytuya').setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

async def test():
    try:
        # Using a slightly different connection approach by avoiding p.detect_available_dps() first
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key='rxK|P`^b6]q2Edcf',
                          protocol_version=3.4, enable_debug=True, timeout=10)
        print("Connected.")
        
        # Manually query status
        res = await p.status()
        print("Status success!", res)
        p.transport.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
