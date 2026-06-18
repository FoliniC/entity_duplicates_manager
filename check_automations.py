import json

with open('.storage/core.entity_registry', 'r') as f:
    data = json.load(f)
    entities = data['data']['entities']
    auto_entities = [e['entity_id'] for e in entities if e['entity_id'].startswith('automation.')]
    for te in sorted(auto_entities):
        print(te)
