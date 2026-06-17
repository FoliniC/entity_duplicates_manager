import json
import os
import shutil

config_path = ".storage/core.config_entries"
backup_path = ".storage/core.config_entries.bak_before_fix"
fixed_path = ".storage/core.config_entries.fixed"

if not os.path.exists(config_path):
    print(f"Error: {config_path} not found.")
    exit(1)

with open(config_path, "r") as f:
    data = json.load(f)

changes_made = 0

for entry in data["data"]["entries"]:
    if entry.get("domain") == "localtuya":
        devices = entry.get("data", {}).get("devices", {})
        for dev_id, dev_config in devices.items():
            entities = dev_config.get("entities", [])
            for ent in entities:
                ent_name = ent.get("friendly_name", ent.get("id"))
                
                # Fix Energy state_class
                if ent.get("device_class") == "energy" and ent.get("state_class") == "measurement":
                    print(f"Fixing '{ent_name}': state_class measurement -> total_increasing")
                    ent["state_class"] = "total_increasing"
                    changes_made += 1
                
                # Fix Voltage unit
                if ent.get("device_class") == "voltage" and ent.get("unit_of_measurement") is None:
                    print(f"Fixing '{ent_name}': unit_of_measurement None -> V")
                    ent["unit_of_measurement"] = "V"
                    changes_made += 1

if changes_made > 0:
    with open(fixed_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nSUCCESS: {changes_made} changes applied.")
    print(f"Fixed file saved to: {fixed_path}")
    print("\nINSTRUCTIONS TO APPLY:")
    print("1. Stop Home Assistant container: 'docker stop homeassistant'")
    print(f"2. Backup current config: 'cp {config_path} {backup_path}'")
    print(f"3. Apply fix: 'cp {fixed_path} {config_path}'")
    print("4. Start Home Assistant container: 'docker start homeassistant'")
else:
    print("No issues found that require fixing.")
