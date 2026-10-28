import sys
sys.path.insert(0, '/config')
from homeassistant.core import HomeAssistant
import asyncio

async def test():
    hass = HomeAssistant('/config')
    await hass.async_start()
    
    # Test send_text_command stop on cucina device
    result = await hass.services.async_call(
        'alexa_devices', 
        'send_text_command', 
        {
            'device_id': '9f7fa85d1597bcdd4948d75d1524dad8',
            'text_command': 'stop'
        }, 
        blocking=True,
        return_response=True
    )
    print(f"Result: {result}")
    
    await hass.async_stop()

asyncio.run(test())