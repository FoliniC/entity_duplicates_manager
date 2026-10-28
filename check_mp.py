import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'].startswith('media_player.') and ('cucina' in e['entity_id'] or 'echo' in e['entity_id'] or 'sistema' in e['entity_id']):
        print(f"{e['entity_id']}: platform={e['platform']}, name={e.get('original_name','')}, disabled={e.get('disabled_by','')}")