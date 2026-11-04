import json
data = json.load(open('/config/.storage/core.config_entries'))
for e in data['data']['entries']:
    if e['domain'] == 'alexa_devices':
        e['disabled_by'] = 'user'
        print(f'Disabled alexa_devices: {e["entry_id"]}')
        break
with open('/config/.storage/core.config_entries', 'w') as f:
    json.dump(data, f, indent=2)