import json
data = json.load(open('/config/.storage/core.entity_registry'))
for e in data['data']['entities']:
    name = e.get('name') or ''
    if e['entity_id'].startswith('media_player.') and ('camera' in e['entity_id'] or 'camera' in name.lower()):
        print(f"{e['entity_id']}: platform={e['platform']}, disabled={e.get('disabled_by')}, name={name}, unique_id={e.get('unique_id')}")
    # Also check for any entity with unique_id containing G0922K073243037A
    if 'G0922K073243037A' in e.get('unique_id', ''):
        print(f"  -> {e['entity_id']}: platform={e['platform']}, disabled={e.get('disabled_by')}")