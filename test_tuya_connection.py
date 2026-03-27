import sys
import os
import asyncio
import logging
import json

# Add temp pytuya path
sys.path.insert(0, "/root/.gemini/tmp/pytuya_test")

from pytuya import TuyaProtocol, TuyaListener

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TuyaTest")

class MyListener(TuyaListener):
    def __init__(self):
        self.sub_devices = {}
        self.connected = False
        
    def status_updated(self, status):
        logger.info(f"STATUS UPDATED: {status}")

    def disconnected(self, exc=""):
        logger.info(f"DISCONNECTED: {exc}")
        self.connected = False

    def subdevice_state_updated(self, state):
        logger.info(f"SUBDEVICE STATE: {state}")

async def test_version(version):
    logger.info(f"Testing protocol version {version}...")
    listener = MyListener()
    
    dev_id = "bf515b512c0fdd0965wqux"
    address = "192.168.0.129"
    local_key = "{W<M+{VJ'@d3cmVk"
    
    loop = asyncio.get_running_loop()
    
    transport = None
    protocol = None
    try:
        transport, protocol = await loop.create_connection(
            lambda: TuyaProtocol(dev_id, local_key, version, True, listener),
            address,
            6668
        )
        listener.connected = True
        logger.info("Socket connected.")
        
        # Request status immediately to trigger handshake
        logger.info("Requesting status...")
        res = await protocol.status()
        logger.info(f"Result for {version}: {res}")
        
        if not listener.connected:
             logger.error("Listener reports disconnected.")
             return False

        if not res and version >= 3.4:
             # Empty result on 3.4 might mean negotiation failed
             logger.warning("Empty result.")
             # Check if we are still connected
             if protocol.transport.is_closing():
                 return False

        await protocol.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed with version {version}: {e}")
        if transport:
            transport.close()
        return False

async def main():
    # Try 3.4 
    if await test_version(3.4):
        logger.info("Version 3.4 WORKED!")
    else:
        logger.info("Version 3.4 FAILED.")

    # Try 3.5
    if await test_version(3.5):
        logger.info("Version 3.5 WORKED!")
    else:
        logger.info("Version 3.5 FAILED.")

    # Try 3.3
    if await test_version(3.3):
        logger.info("Version 3.3 WORKED!")
    else:
        logger.info("Version 3.3 FAILED.")

    # Try 3.1
    if await test_version(3.1):
        logger.info("Version 3.1 WORKED!")
    else:
        logger.info("Version 3.1 FAILED.")

if __name__ == "__main__":
    asyncio.run(main())
