import os
import re

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Logica di iniezione ultra-aggressiva: 
# Non importa cosa dice il dispositivo, se è il Garage, mostriamo TUTTI i DP che conosciamo.
# Modifichiamo il punto in cui viene popolata la lista 'detected_dps'

# 1. Cerchiamo il punto in cui 'detected_dps' viene loggato
target_log = 'logger.info("Total DPS detected: %s", detected_dps)'

robust_injection = """    # v1.0.31 - Forced DP Injection for Garage Door
    if data.get("device_id") == "bf27acf38b97deb8d9ogjj" or data.get("friendly_name") == "Garage Door":
        for d in ["1", "2", "3", "4", "5", "12"]:
            if str(d) not in detected_dps:
                detected_dps[str(d)] = -1
        logger.info("Forced Garage DPs: %s", detected_dps)
    
    logger.info("Total DPS detected: %s", detected_dps)"""

if target_log in content:
    updated_content = content.replace(target_log, robust_injection)
    with open(file_path, 'w') as f:
        f.write(updated_content)
    print("SUCCESS: Config Flow patched with Ultra-Forced Injection.")
else:
    # Fallback: se la patch precedente ha cambiato il log
    if 'logger.info("Total DPS: %s", detected_dps)' in content:
        updated_content = content.replace('logger.info("Total DPS: %s", detected_dps)', robust_injection)
        with open(file_path, 'w') as f:
            f.write(updated_content)
        print("SUCCESS: Config Flow patched (fallback method).")
    else:
        print("ERROR: Could not find target log line.")
