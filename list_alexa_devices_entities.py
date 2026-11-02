import json
data = json.load(open('/config/.storage/core.entity_registry'))
alexa_devices_entities = [e for e in data['data']['entities'] if e['platform'] == 'alexa_devices']
print(f'Totale entità alexa_devices: {len(alexa_devices_entities)}')
for e in alexa_devices_entities:
    domain = e['entity_id'].split('.')[0]
    print(f'  {e["entity_id"]}: domain={domain}, disabled={e.get("disabled_by")}')