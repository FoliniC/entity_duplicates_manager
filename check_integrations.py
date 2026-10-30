import json
data = json.load(open('/config/.storage/core.config_entries'))
for e in data['data']['entries']:
    if e['domain'] in ['emulated_hue', 'alexa_media', 'homeassistant']:
        print(f'Domain: {e["domain"]}, title: {e.get("title")}, disabled: {e.get("disabled_by")}')