import asyncio
import logging
import subprocess
import time
from modbuslink import AsyncTcpTransport, AsyncModbusClient

# Configurazione
ALFA_IP = "192.168.0.101"
ALFA_PORT = 502
SLAVE_ID = 1
LIGHT_ADDR = 2
FULL_BATCH = (2, 5) # Esempio: leggi 5 registri partendo dal 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
_LOGGER = logging.getLogger(__name__)

def check_system_sockets():
    """Verifica a livello di OS se ci sono socket aperti verso l'IP di Alfa."""
    try:
        # Cerchiamo connessioni verso l'IP di Alfa (qualsiasi stato)
        cmd = f"ss -atn | grep {ALFA_IP}:{ALFA_PORT}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        _LOGGER.error(f"Errore nel controllo dei socket: {e}")
        return ""

async def wait_for_clean_sockets(timeout=30):
    """Attende finché il sistema non ha liberato tutti i socket verso Alfa."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        sockets = check_system_sockets()
        if not sockets:
            _LOGGER.info("Sistema pulito: nessun socket aperto verso Alfa.")
            return True
        _LOGGER.info(f"Socket ancora attivi/in attesa verso {ALFA_IP}...")
        await asyncio.sleep(2)
    _LOGGER.warning("Timeout attesa pulizia socket, procedo comunque.")
    return False

async def robust_test_cycle(cycle_id):
    _LOGGER.info(f"=== INIZIO CICLO {cycle_id} ===")
    
    # 1. Assicuriamoci che il sistema sia pulito
    await wait_for_clean_sockets()
    
    transport = AsyncTcpTransport(host=ALFA_IP, port=ALFA_PORT, timeout=10)
    client = AsyncModbusClient(transport)
    
    success = False
    try:
        # Gestione manuale del transport per massimo controllo
        await transport.open()
        _LOGGER.info("Connessione TCP stabilita.")
        
        # 2. LIGHT CALL: Un solo registro
        _LOGGER.info(f"Eseguo Light Call (ADDR {LIGHT_ADDR})...")
        try:
            res_light = await asyncio.wait_for(
                client.read_holding_registers(slave_id=SLAVE_ID, start_address=LIGHT_ADDR, quantity=1),
                timeout=5
            )
            _LOGGER.info(f"Light Call RIUSCITA: {res_light}")
            
            # 3. Se la light call passa, proviamo una lettura più corposa
            await asyncio.sleep(1)
            _LOGGER.info("Eseguo Full Read...")
            res_full = await client.read_holding_registers(slave_id=SLAVE_ID, start_address=FULL_BATCH[0], quantity=FULL_BATCH[1])
            _LOGGER.info(f"Full Read RIUSCITA: {res_full}")
            success = True
            
        except asyncio.TimeoutError:
            _LOGGER.error("Light Call fallita per TIMEOUT.")
        except Exception as e:
            _LOGGER.error(f"Errore durante lo scambio dati Modbus: {e}")
        
        # Chiusura esplicita
        await transport.close()
        _LOGGER.info("Connessione TCP chiusa correttamente.")
                
    except Exception as e:
        _LOGGER.error(f"Impossibile gestire la connessione TCP: {e}")
        try: await transport.close()
        except: pass
    
    _LOGGER.info(f"=== FINE CICLO {cycle_id} (Successo: {success}) ===")
    return success

async def main():
    for i in range(1, 6): # Eseguiamo 5 cicli di test
        await robust_test_cycle(i)
        _LOGGER.info("Attesa 15 secondi tra un ciclo e l'altro...")
        await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
