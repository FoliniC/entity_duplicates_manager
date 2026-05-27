import os
import re

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Semplifichiamo al massimo per evitare l'eccezione di update
new_forced_gen = """        dev_data = gen_localtuya_entities(localtuya_data, category)
        
        if dev_id == "bf27acf38b97deb8d9ogjj":
            _LOGGER.error("[ULTIMATE-FIX] Applying STABLE DP mapping for Garage (Cover + Contact)")
            dev_data = [
                {
                    "friendly_name": "Garage Door",
                    "id": 1,
                    "platform": "cover",
                    "device_class": "garage",
                    "commands_set": "open_close_stop",
                    "positioning_mode": "none",
                    "current_position_dp": 3,
                    "position_inverted": True
                },
                {
                    "friendly_name": "Garage Contact",
                    "id": 3,
                    "platform": "binary_sensor",
                    "device_class": "garage_door"
                }
            ]"""

# Sostituiamo il blocco precedente (v1.0.38)
pattern = re.compile(r'if dev_id == "bf27acf38b97deb8d9ogjj":.*?\[ULTIMATE-FIX\].*?\]', re.DOTALL)

if pattern.search(content):
    updated = pattern.sub(new_forced_gen, content)
    with open(file_path, 'w') as f:
        f.write(updated)
    print("SUCCESS: Garage mapping simplified for stability.")
else:
    print("ERROR: Could not find block to replace.")
