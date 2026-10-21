import json

with open('/config/.storage/core.config_entries', 'r') as f:
    data = json.load(f)

# Remove xiaomi_ble entry
data['data']['entries'] = [e for e in data['data']['entries'] if e['domain'] != 'xiaomi_ble']

with open('/config/.storage/core.config_entries', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Removed xiaomi_ble entry')