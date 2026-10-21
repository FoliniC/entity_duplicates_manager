import json

with open('/config/.storage/core.config_entries', 'r') as f:
    data = json.load(f)

for entry in data['data']['entries']:
    if entry['domain'] == 'xiaomi_ble':
        entry['data'] = {
            "bindkey": "926c7b92ffd7b7e4ff10cceaa1c39884"
        }
        entry['modified_at'] = '2026-10-20T23:45:00.000000+00:00'
        print(f"Added bindkey to entry {entry['entry_id']}")
        break

with open('/config/.storage/core.config_entries', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Saved')