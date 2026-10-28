import asyncio
import aiohttp

async def test():
    # Try to call the service via supervisor token
    token = open('/run/secrets/hassio_token').read().strip() if open('/run/secrets/hassio_token', 'r').readable() else None
    if not token:
        print("No supervisor token")
        return
    
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # Test send_text_command with stop
        async with session.post(
            'http://supervisor/core/api/services/alexa_devices/send_text_command',
            headers=headers,
            json={'device_id': '9f7fa85d1597bcdd4948d75d1524dad8', 'text_command': 'stop'}
        ) as resp:
            print(f"Status: {resp.status}")
            print(await resp.text())

asyncio.run(test())