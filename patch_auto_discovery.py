import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# MODIFICA: Intercettiamo il risultato di gen_localtuya_entities
# e se è il nostro garage, forziamo la lista completa delle entità che vogliamo.

old_gen_call = "        dev_data = gen_localtuya_entities(localtuya_data, category)"

new_forced_gen = """        dev_data = gen_localtuya_entities(localtuya_data, category)
        
        # v1.0.36 - Forced Auto-Discovery expansion for Garage
        if dev_id == "bf27acf38b97deb8d9ogjj":
            _LOGGER.error("[ULTIMATE-FIX] Overriding auto-discovery for Garage with full entity set")
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
                    "friendly_name": "Garage Switch",
                    "id": 1,
                    "platform": "switch"
                },
                {
                    "friendly_name": "Garage Contact",
                    "id": 3,
                    "platform": "binary_sensor",
                    "device_class": "garage_door"
                },
                {
                    "friendly_name": "Door State",
                    "id": 12,
                    "platform": "sensor"
                }
            ]"""

if old_gen_call in content:
    updated = content.replace(old_gen_call, new_forced_gen)
    with open(file_path, 'w') as f:
        f.write(updated)
    print("SUCCESS: Auto-discovery logic patched.")
else:
    print("ERROR: Could not find gen_localtuya_entities call.")
