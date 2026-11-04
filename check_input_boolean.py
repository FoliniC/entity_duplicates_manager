import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'] == 'input_boolean.alexa_accendi_uscita':
        print(f'Entity: {e["entity_id"]}')
        break