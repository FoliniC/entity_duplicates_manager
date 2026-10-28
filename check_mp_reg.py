import json
data = json.load(open('/config/.storage/core.entity_registry'))
mps = [e for e in data['data']['entities'] if e['entity_id'].startswith('media_player.') and ('cucina' in e['entity_id'] or 'sistema' in e['entity_id'])]
for a in mps:
    print(f"{a['entity_id']}: platform={a['platform']}, disabled={a.get('disabled_by','')}")