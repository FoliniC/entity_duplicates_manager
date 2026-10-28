import json
data = json.load(open('/config/.storage/core.entity_registry'))
ibs = [e for e in data['data']['entities'] if e['entity_id'].startswith('input_boolean.') and 'alexa' in e['entity_id']]
for a in ibs:
    print(f"{a['entity_id']}: {a.get('original_name','')}")