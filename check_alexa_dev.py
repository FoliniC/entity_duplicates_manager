import json
data = json.load(open('/config/.storage/core.config_entries'))
for e in data['data']['entries']:
    if e['domain'] == 'alexa_devices':
        print(f"entry_id: {e['entry_id']}")
        print(f"disabled_by: {e.get('disabled_by')}")