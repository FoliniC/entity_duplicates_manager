import sys
sys.path.insert(0, '/config')
from homeassistant.core import HomeAssistant
import asyncio

async def test():
    hass = HomeAssistant('/config')
    await hass.async_start()
    
    # Test media_stop on media_player.cucina
    await hass.services.async_call('media_player', 'media_stop', {'entity_id': 'media_player.cucina'}, blocking=True)
    print('media_stop called on media_player.cucina')
    
    # Check state
    state = hass.states.get('media_player.cucina')
    print(f'State after stop: {state.state if state else "NOT FOUND"}')
    
    await hass.async_stop()

asyncio.run(test())