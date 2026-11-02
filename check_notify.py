import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['platform'] == 'alexa_media' and e['entity_id'].startswith('notify.'):
        print(f'{e["entity_id"]}: name={e.get("name")}')
    if e['platform'] == 'alexa_devices' and e['entity_id'].startswith('notify.'):
        print(f'  [alexa_devices] {e["entity_id"]}: name={e.get("name")}')