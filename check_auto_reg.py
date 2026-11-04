import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'] == 'automation.alexa_modalita_uscita':
        print(f'Automation: {e["entity_id"]}, platform={e["platform"]}, disabled={e.get("disabled_by")}')
        break
else:
    print('Automation NOT FOUND in entity registry')