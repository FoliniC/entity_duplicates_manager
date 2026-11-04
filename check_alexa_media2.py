import json
data = json.load(open('/config/.storage/core.config_entries'))
for e in data['data']['entries']:
    if e['domain'] == 'alexa_media':
        print(f'alexa_media disabled_by: {e.get("disabled_by")}')
        break