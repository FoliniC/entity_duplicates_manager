import asyncio
import sys
sys.path.insert(0, '/config')

from homeassistant.core import HomeAssistant
from homeassistant.helpers import service

async def test():
    # Get the HA instance
    hass = HomeAssistant()
    await hass.async_start()
    
    # Call light.turn_on for light.uscita
    await hass.services.async_call('light', 'turn_on', {'entity_id': 'light.uscita'})
    
    await hass.async_stop()

asyncio.run(test())