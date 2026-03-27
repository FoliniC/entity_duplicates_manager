import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Definizione pulita delle entità per il Garage
# Usiamo nomi brevi perché HA aggiungerà comunque il nome del dispositivo come prefisso se configurato così
new_forced_gen = """        dev_data = gen_localtuya_entities(localtuya_data, category)
        
        if dev_id == "bf27acf38b97deb8d9ogjj":
            _LOGGER.error("[ULTIMATE-FIX] Applying CLEAN entity names for Garage")
            dev_data = [
                {
                    "friendly_name": "Door",
                    "id": 1,
                    "platform": "cover",
                    "device_class": "garage",
                    "commands_set": "open_close_stop",
                    "positioning_mode": "none",
                    "current_position_dp": 3,
                    "position_inverted": True
                },
                {
                    "friendly_name": "Relay",
                    "id": 1,
                    "platform": "switch"
                },
                {
                    "friendly_name": "Sensor",
                    "id": 3,
                    "platform": "binary_sensor",
                    "device_class": "garage_door"
                },
                {
                    "friendly_name": "Status Code",
                    "id": 12,
                    "platform": "sensor"
                }
            ]
            _LOGGER.error(f"[ULTIMATE-FIX] Final entities to be added: {[e['friendly_name'] for e in dev_data]}")"""

# Sostituiamo il blocco precedente
import re
pattern = re.compile(r'dev_data = gen_localtuya_entities\(localtuya_data, category\).*?\[ULTIMATE-FIX\].*?\]', re.DOTALL)

if pattern.search(content):
    updated = pattern.sub(new_forced_gen, content)
    with open(file_path, 'w') as f:
        f.write(updated)
    print("SUCCESS: Garage entity names cleaned.")
else:
    print("ERROR: Could not find previous block to replace.")
