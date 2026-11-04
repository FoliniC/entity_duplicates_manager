import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'] == 'media_player.cucina':
        print(f'{e["entity_id"]}: platform={e["platform"]}, disabled={e.get("disabled_by")}')
        break