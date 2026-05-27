import json
with open('.storage/core.config_entries', 'r') as f:
    data = json.load(f)
    for entry in data.get("data", {}).get("entries", []):
        if entry["domain"] == "localtuya":
            dev = entry["data"]["devices"]["bf0e2041fb7f7875c4bcss"]
            print(f"Device ID: {dev['device_id']}")
            print(f"Local Key: {dev['local_key']}")
