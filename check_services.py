import json
data = json.load(open('/config/.storage/core.service_registry'))
for s in data['data']['services']:
    if 'alexa' in s.get('domain','') or 'alexa' in s.get('service',''):
        print(f"{s.get('domain')}.{s.get('service')}: {s.get('description','')}")