import json

with open('/config/.storage/core.entity_registry', 'r') as f:
    data = json.load(f)
    entities = data['data']['entities']
    alexa_switches = [e for e in entities if e['entity_id'].startswith('switch.alexa')]
    for e in alexa_switches:
        print(f'{e["entity_id"]}: platform={e.get("platform")}')