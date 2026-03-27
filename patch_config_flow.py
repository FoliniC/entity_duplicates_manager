import os

file_path = "/config/custom_components/localtuya/config_flow.py"
backup_path = "/config/custom_components/localtuya/config_flow.py.bak"

with open(file_path, 'r') as f:
    content = f.read()

# MODIFICA 1: Aumentiamo il timeout da 5 a 15 secondi per dare tempo al protocollo 3.4
old_timeout = "async with asyncio.timeout(5):"
new_timeout = "async with asyncio.timeout(15):"

# MODIFICA 2: Aggiungiamo un heartbeat e un piccolo delay prima di detect_available_dps
# per svegliare il dispositivo durante la configurazione iniziale.
old_detect = """                        logger.info(f"Connected attempt to detect the device DPS")
                        detected_dps = await interface.detect_available_dps(cid=cid)"""

new_detect = """                        logger.info(f"Connected attempt to detect the device DPS (v1.0.27 - Robust flow)")
                        # Wake up sequence for reliable discovery
                        try:
                            await interface.heartbeat()
                            await asyncio.sleep(0.5)
                            await interface.update_dps()
                            await asyncio.sleep(0.5)
                        except:
                            pass
                        detected_dps = await interface.detect_available_dps(cid=cid)"""

if old_timeout in content and old_detect in content:
    if not os.path.exists(backup_path):
        os.rename(file_path, backup_path)
    
    updated_content = content.replace(old_timeout, new_timeout).replace(old_detect, new_detect)
    
    with open(file_path, 'w') as f:
        f.write(updated_content)
    print("SUCCESS: Config Flow patched for robust DP discovery.")
else:
    print("ERROR: Could not find target code in config_flow.py.")
