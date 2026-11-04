import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    if e['entity_id'] in ['media_player.2o_echo_dot_di_carlo', 'media_player.echo_dot_di_carlo']:
        print(f'{e["entity_id"]}: platform={e["platform"]}, disabled={e.get("disabled_by")}')