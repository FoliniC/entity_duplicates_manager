import json
data = json.load(open('/config/.storage/core.config_entries'))
for e in data['data']['entries']:
    if e['domain'] == 'alexa_devices':
        print('Data:')
        print(json.dumps(e.get('data', {}), indent=2))