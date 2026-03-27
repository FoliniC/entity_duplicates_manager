import os
import re

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Ricostruiamo l'intera funzione in modo perfetto
clean_function = """    async def async_step_auto_configure_device(self, user_input=None):
        """Handle asking which templates to use"""

        errors = {}
        placeholders = {}

        # Gather the information
        is_cloud = not self.config_entry.data.get("no_cloud")
        dev_id = self.selected_device
        category = None
        node_id = self.nodeID
        device_data = self.cloud_data.device_list.get(dev_id)
        if device_data:
            category = self.cloud_data.device_list[dev_id].get("category", "")

        localtuya_data = {
            "device_cloud_data": device_data,
            "dps_strings": self.dps_strings,
            "friendly_name": self.device_data.get("friendly_name"),
        }

        dev_data = gen_localtuya_entities(localtuya_data, category)
        
        # v1.0.39 - STABLE mapping for Garage
        if dev_id == "bf27acf38b97deb8d9ogjj":
            _LOGGER.error("[ULTIMATE-FIX] Overriding for Garage (Stable set)")
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
            ]

        if dev_data:
            self.entities = dev_data
            return await self.async_step_pick_entity_type(
                {"no_additional_entities": True}
            )"""

# Cerchiamo l'inizio della funzione e sostituiamo TUTTO il blocco fino alla chiusura del return
pattern = re.compile(r'    async def async_step_auto_configure_device\(self, user_input=None\):.*?\{"no_additional_entities": True\}\s+\)', re.DOTALL)

if pattern.search(content):
    updated = pattern.sub(clean_function, content)
    with open(file_path, 'w') as f:
        f.write(updated)
    print("SUCCESS")
else:
    # Se il pattern precedente fallisce per via delle doppie patch, usiamo un metodo più "bruto"
    print("MATCH FAILED, trying fallback...")
    # Troviamo la riga d'inizio
    start_marker = '    async def async_step_auto_configure_device(self, user_input=None):'
    # Troviamo la riga di fine (inizio della funzione successiva)
    end_marker = '    async def async_step_choose_template(self, user_input=None):'
    
    if start_marker in content and end_marker in content:
        parts = content.split(start_marker)
        rest = parts[1].split(end_marker)
        new_content = parts[0] + clean_function + "

" + end_marker + rest[1]
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("SUCCESS (fallback)")
    else:
        print("ERROR: Markers not found")
