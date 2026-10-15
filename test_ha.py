import asyncio
import sys
sys.path.insert(0, '/config')

from homeassistant.core import HomeAssistant
from homeassistant.helpers import service

async def test():
    # This won't work without a running HA instance reference
    pass

print("OK")