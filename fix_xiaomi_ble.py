import json

with open('/config/.storage/core.config_entries', 'r') as f:
    data = json.load(f)

for entry in data['data']['entries']:
    if entry['domain'] == 'xiaomi_ble':
        entry['source'] = 'user'
        entry['modified_at'] = '2026-10-20T23:30:00.000000+00:00'
        print(f"Changed source from 'ignore' to 'user' for entry {entry['entry_id']}")
        break

with open('/config/.storage/core.config_entries', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Saved')