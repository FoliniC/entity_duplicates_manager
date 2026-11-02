import json
data = json.load(open('/config/.storage/core.device_registry'))
for d in data['data']['devices']:
    if d['id'] in ['9f7fa85d1597bcdd4948d75d1524dad8', 'e029aab2768927141cbfaf737132ed29']:
        print(f'Device: {d["id"]} - name: {d.get("name")} - name_by_user: {d.get("name_by_user")}')
        for ident in d.get('identifiers', []):
            print(f'  Identifier: {ident}')