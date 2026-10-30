import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    uid = e.get('unique_id', '')
    if 'uscita' in uid or 'alexa_uscita' in uid:
        print(f'{e["entity_id"]}: platform={e["platform"]}, unique_id={uid}, name={e.get("name")}')