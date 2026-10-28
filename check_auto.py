import sys
sys.path.insert(0, '/config')
from homeassistant.core import HomeAssistant
import asyncio

async def test():
    hass = HomeAssistant('/config')
    await hass.async_start()
    
    # Check if automation is loaded
    auto = hass.states.get('automation.alexa_modalita_uscita')
    print(f"Automation state: {auto.state if auto else 'NOT FOUND'}")
    if auto:
        print(f"  Attributes: {dict(auto.attributes)}")
    
    # Check input_boolean
    ib = hass.states.get('input_boolean.alexa_accendi_uscita')
    print(f"Input boolean: {ib.state if ib else 'NOT FOUND'}")
    
    # Check media_player states
    for mp in ['media_player.cucina', 'media_player.sistema_audio']:
        st = hass.states.get(mp)
        print(f"{mp}: {st.state if st else 'NOT FOUND'}")
        if st:
            print(f"  Attributes: {dict(st.attributes)}")
    
    await hass.async_stop()

asyncio.run(test())