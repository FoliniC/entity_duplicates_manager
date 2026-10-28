import json
data = json.load(open('/config/.storage/core.device_registry'))
# Find Carlo's M67beta
target_id = None
for d in data['data']['devices']:
    name = d.get('name', '')
    name_by_user = d.get('name_by_user', '')
    if 'M67beta' in name or 'M67beta' in (name_by_user or ''):
        target_id = d['id']
        print(f"Found: {d['id']} - name: {name} - name_by_user: {name_by_user} - identifiers: {d.get('identifiers')}")
        break

if target_id:
    # Remove from device registry
    data['data']['devices'] = [d for d in data['data']['devices'] if d['id'] != target_id]
    with open('/config/.storage/core.device_registry', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Removed device {target_id}")
else:
    print("Device not found")