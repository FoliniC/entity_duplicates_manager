import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if 'uscita' in e['entity_id'] or 'uscita' in (e.get('name') or ''):
        print(f'{e["entity_id"]}: platform={e["platform"]}, disabled={e.get("disabled_by")}, name={e.get("name")}')