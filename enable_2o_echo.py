import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'] == 'media_player.2o_echo_dot_di_carlo':
        e['disabled_by'] = None
        print(f"Abilitato {e['entity_id']}")
        break
with open('/config/.storage/core.entity_registry', 'w') as f:
    json.dump(data, f, indent=2)