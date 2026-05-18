import sys
sys.path.insert(0, '/home/carlo/docker/homeassistant/config/custom_components/localtuya/core')
import json
from pathlib import Path

# Mocking the function that loads devices
def get_devices_data():
    ha_config = Path("/home/carlo/docker/homeassistant/config/.storage/core.config_entries")
    with open(ha_config, 'r') as f:
        data = json.load(f)
        for entry in data.get("data", {}).get("entries", []):
            if entry["domain"] == "localtuya":
                return entry["data"]["devices"]
    return {}

devices = get_devices_data()
d = devices.get('bf0e2041fb7f7875c4bcss')
print(f"Device Data: {d}")
