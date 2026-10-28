import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'] == 'media_player.2o_echo_dot_di_carlo':
        print(f"disabled_by: {e.get('disabled_by')}")
        break