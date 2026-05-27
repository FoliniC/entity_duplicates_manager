import os
import re

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

new_function_body = """    async def async_step_auto_configure_device(self, user_input=None):
        \"\"\"Handle asking which templates to use\"\"\"

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
        
        if dev_id == "bf27acf38b97deb8d9ogjj":
            _LOGGER.error("[ULTIMATE-FIX] Overriding auto-discovery for Garage with UNIQUE DP set")
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
                    "friendly_name": "Contact",
                    "id": 3,
                    "platform": "binary_sensor",
                    "device_class": "garage_door"
                },
                {
                    "friendly_name": "Status",
                    "id": 12,
                    "platform": "sensor"
                }
            ]

        if dev_data:
            self.entities = dev_data
            return await self.async_step_pick_entity_type(
                {"no_additional_entities": True}
            )"""

pattern = re.compile(r'    async def async_step_auto_configure_device\(self, user_input=None\):.*?\{NO_ADDITIONAL_ENTITIES: True\}\s+\)', re.DOTALL)

if pattern.search(content):
    updated = pattern.sub(new_function_body, content)
    with open(file_path, 'w') as f:
        f.write(updated)
    print("SUCCESS")
else:
    print("ERROR: Match failed")
