import json

with open('.storage/core.restore_state', 'r') as f:
    data = json.load(f)
    states = data['data']
    for s in states:
        eid = s['state']['entity_id']
        if 'logging' in eid:
            print(f"{eid}: {s['state']['state']}")
