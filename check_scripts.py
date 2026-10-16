import asyncio
import sys
sys.path.insert(0, '/usr/src/homeassistant')

from homeassistant.core import HomeAssistant

async def check_scripts():
    hass = HomeAssistant()
    await hass.async_start()
    
    # Check for alexa scripts
    for state in hass.states.async_all():
        if 'alexa' in state.entity_id:
            print(f"Found: {state.entity_id} = {state.state}")
    
    await hass.async_stop()

asyncio.run(check_scripts())