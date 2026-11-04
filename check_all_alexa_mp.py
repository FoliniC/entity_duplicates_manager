import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['platform'] == 'alexa_media' and e['entity_id'].startswith('media_player.'):
        print(f'{e["entity_id"]}: disabled={e.get("disabled_by")}')