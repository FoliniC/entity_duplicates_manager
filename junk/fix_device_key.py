import json
import os

entries_path = '.storage/core.config_entries'
with open(entries_path, 'r') as f:
    data = json.load(f)

# Iterate and update the key for the device
for entry in data.get("data", {}).get("entries", []):
    if entry["domain"] == "localtuya":
        dev = entry["data"]["devices"].get('bf0e2041fb7f7875c4bcss')
        if dev:
            print(f"Old key: {dev['local_key']}")
            dev['local_key'] = 'rxK|P`^b6]q2Edcf'
            print(f"New key: {dev['local_key']}")

with open(entries_path + '.new', 'w') as f:
    json.dump(data, f, indent=2)
