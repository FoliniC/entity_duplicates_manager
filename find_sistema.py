import json
data = json.load(open('/config/.storage/core.device_registry'))
for d in data['data']['devices']:
    name = d.get('name', '')
    name_by_user = d.get('name_by_user', '')
    if 'sistema' in name.lower() or 'sistema' in (name_by_user or '').lower():
        print(f"Device: {d['id']} - name: {name} - name_by_user: {name_by_user} - identifiers: {d.get('identifiers')}")