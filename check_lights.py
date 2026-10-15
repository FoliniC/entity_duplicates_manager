import json

with open('/config/.storage/core.entity_registry', 'r') as f:
    data = json.load(f)
    entities = data['data']['entities']
    light_entities = [e['entity_id'] for e in entities if e['entity_id'].startswith('light.')]
    alexa_lights = [e for e in light_entities if any(x in e for x in ['uscita', 'entrata', 'ritorno', 'verifica', 'buongiorno'])]
    for e in sorted(alexa_lights):
        print(e)