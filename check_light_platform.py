import json

with open('/config/.storage/core.entity_registry', 'r') as f:
    data = json.load(f)
    entities = data['data']['entities']
    alexa_lights = [e for e in entities if e['entity_id'] in ['light.uscita', 'light.entrata', 'light.ritorno_a_casa', 'light.verifica', 'light.buongiorno']]
    for e in alexa_lights:
        print(f"{e['entity_id']}: platform={e.get('platform')}, unique_id={e.get('unique_id')}")