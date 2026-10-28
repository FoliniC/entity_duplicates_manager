import json
data = json.load(open('/config/.storage/core.restore_state'))
for s in data:
    if isinstance(s, dict) and s.get('entity_id','').startswith('media_player.'):
        if 'cucina' in s['entity_id'] or 'sistema' in s['entity_id'] or 'echo' in s['entity_id']:
            print(f"{s['entity_id']}: state={s.get('state')}")