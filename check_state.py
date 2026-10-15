import json

with open('/config/.storage/core.restore_state', 'r') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2)[:5000])