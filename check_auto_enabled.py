import json

with open('/config/.storage/core.entity_registry', 'r') as f:
    data = json.load(f)
    entities = data['data']['entities']
    alexa_auto = [e for e in entities if e['entity_id'].startswith('automation.alexa')]
    for e in alexa_auto:
        print(f"{e['entity_id']}: disabled={e.get('disabled', False)}, disabled_by={e.get('disabled_by')}")