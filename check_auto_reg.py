import json
data = json.load(open('/config/.storage/core.entity_registry'))
autos = [e for e in data['data']['entities'] if e['entity_id'].startswith('automation.') and 'alexa' in e['entity_id']]
for a in autos:
    print(f"{a['entity_id']}: {a.get('original_name','')}")