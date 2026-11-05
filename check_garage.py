import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if 'garage' in e['entity_id'] or 'wifi_garage' in e['entity_id']:
        print(f'{e["entity_id"]}: platform={e["platform"]}, disabled={e.get("disabled_by")}')