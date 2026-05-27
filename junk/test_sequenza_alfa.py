import asyncio
import logging
from modbuslink import AsyncTcpTransport, AsyncModbusClient

ALFA_IP = "192.168.0.101"
ALFA_PORT = 502

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

async def run_fast_test():
    _LOGGER.info("--- FAST TEST (NO SLEEP) ---")
    transport = AsyncTcpTransport(host=ALFA_IP, port=ALFA_PORT, timeout=2)
    client = AsyncModbusClient(transport)
    try:
        async with client:
            # Invio immediato
            res = await client.read_holding_registers(slave_id=1, start_address=2, quantity=1)
            _LOGGER.info(f"SUCCESS: {res}")
    except Exception as e:
        _LOGGER.error(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(run_fast_test())