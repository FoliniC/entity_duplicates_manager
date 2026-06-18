import json

with open('.storage/core.entity_registry', 'r') as f:
    data = json.load(f)
    entities = data['data']['entities']
    th_entities = [e['entity_id'] for e in entities if 'th' in e['entity_id']]
    for te in sorted(th_entities):
        print(te)
