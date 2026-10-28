import json
# Test the alexa_devices.send_text_command with "stop"
# Let's check the actual device IDs for cucina and sistema_audio
data = json.load(open('/config/.storage/core.device_registry'))
for d in data['data']['devices']:
    if 'cucina' in d.get('name','').lower() and d.get('identifiers',[])[0][0] == 'alexa_devices':
        print(f"CUCINA: id={d['id']}, identifiers={d.get('identifiers')}")
    if 'sistema' in d.get('name','').lower() and d.get('identifiers',[])[0][0] == 'alexa_devices':
        print(f"SISTEMA: id={d['id']}, identifiers={d.get('identifiers')}")