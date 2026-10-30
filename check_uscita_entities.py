import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'] in ['light.uscita', 'switch.alexa_uscita', 'input_boolean.alexa_accendi_uscita']:
        print(f'{e["entity_id"]}: platform={e["platform"]}, disabled={e.get("disabled_by")}, name={e.get("name")}, unique_id={e.get("unique_id")}')