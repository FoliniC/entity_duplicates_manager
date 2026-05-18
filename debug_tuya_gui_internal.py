import asyncio
import logging
import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
from pytuya import connect, _LOGGER as pytuya_log

class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, record): self.records.append(self.format(record))

async def test():
    h = ListHandler()
    pytuya_log.addHandler(h)
    pytuya_log.setLevel(logging.DEBUG)
    
    try:
        p = await connect(address='192.168.0.18', device_id='bf0e2041fb7f7875c4bcss', local_key='rxK|P`^b6]q2Edcf',
                          protocol_version=3.4, enable_debug=True, timeout=5)
        await p.status()
        print(f"Captured records count: {len(h.records)}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pytuya_log.removeHandler(h)

asyncio.run(test())
