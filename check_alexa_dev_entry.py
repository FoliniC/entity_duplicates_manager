import json
data = json.load(open('/config/.storage/core.config_entries'))
for e in data['data']['entries']:
    if e['domain'] == 'alexa_devices':
        print(f'Domain: {e["domain"]}')
        print(f'Title: {e.get("title")}')
        print(f'Entry ID: {e["entry_id"]}')
        print(f'Disabled: {e.get("disabled_by")}')
        print(f'Data keys: {list(e.get("data", {}).keys())}')
        print(f'Options: {e.get("options")}')