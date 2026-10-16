import asyncio
import sys
sys.path.insert(0, '/usr/src/homeassistant')

from homeassistant.core import HomeAssistant

async def check():
    hass = HomeAssistant('/config')
    await hass.async_start()
    entity = hass.states.get('script.alexa_buongiorno')
    print('Entity:', entity)
    if entity:
        print('State:', entity.state)
        print('Domain:', entity.domain)
    await hass.async_stop()

asyncio.run(check())