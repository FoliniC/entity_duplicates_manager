import json
import os

config_path = ".storage/core.config_entries"

if not os.path.exists(config_path):
    print("Config entries file not found.")
    exit(1)

with open(config_path, "r") as f:
    data = json.load(f)

for entry in data["data"]["entries"]:
    if entry.get("domain") == "localtuya":
        print(f"Entry: {entry['title']} ({entry['entry_id']})")
        devices = entry.get("data", {}).get("devices", {})
        for dev_id, dev_config in devices.items():
            name = dev_config.get("friendly_name", dev_id)
            sleep_time = dev_config.get("device_sleep_time", 0)
            host = dev_config.get("host")
            print(f"  Device: {name:35} IP: {host:15} Sleep: {sleep_time}")
            
            # Check entities for errors mentioned in log
            entities = dev_config.get("entities", [])
            for ent in entities:
                ent_name = ent.get("friendly_name", ent.get("id"))
                if ent.get("device_class") == "energy" and ent.get("state_class") == "measurement":
                    print(f"    !!! ERROR: Entity '{ent_name}' has device_class 'energy' but state_class 'measurement'")
                if ent.get("device_class") == "voltage" and ent.get("unit_of_measurement") is None:
                    print(f"    !!! ERROR: Entity '{ent_name}' has device_class 'voltage' but unit_of_measurement is None")
