import json
data = json.load(open('/config/.storage/core.entity_registry'))
# Find entities belonging to device 16aa61f3c2ddc677dade6585b75b4aed
target_device_id = '16aa61f3c2ddc677dade6585b75b4aed'
to_remove = []
for e in data['data']['entities']:
    if e.get('device_id') == target_device_id:
        to_remove.append(e['entity_id'])

if to_remove:
    print(f"Found {len(to_remove)} entities for device:")
    for eid in to_remove:
        print(f"  - {eid}")
    data['data']['entities'] = [e for e in data['data']['entities'] if e.get('device_id') != target_device_id]
    with open('/config/.storage/core.entity_registry', 'w') as f:
        json.dump(data, f, indent=2)
    print("Removed entities")
else:
    print("No entities found for this device")