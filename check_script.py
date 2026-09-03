import json

d = json.load(open('/config/.storage/core.entity_registry'))
for e in d['data']['entities']:
    if e['entity_id'] == 'script.phone_projection_refresh':
        print('SCRIPT TROVATO:', e['entity_id'])
        print('  name:', e.get('original_name', 'NO NAME'))
        print('  disabled_by:', e.get('disabled_by', 'NO'))
        print('  config_entry_id:', e.get('config_entry_id', 'N/A'))

# Also check the script.yaml storage
import os
scripts_path = '/config/.storage/core.script_registry'
if os.path.exists(scripts_path):
    s = json.load(open(scripts_path))
    print('\nScript registry entries:')
    for item in s.get('data', {}).get('entries', []):
        if 'phone_projection' in item.get('entity_id', ''):
            print(' ', item)
else:
    print('No script registry found at', scripts_path)

# Check the scripts.yaml in packages
pkg_path = '/config/packages/btc_investment_tracker.yaml'
import yaml
with open(pkg_path) as f:
    data = list(yaml.safe_load_all(f))[0]
    scripts = data.get('script', {})
    print('\nScripts defined in package:')
    for name, cfg in scripts.items():
        print(f'  script.{name}')
        if isinstance(cfg, dict) and 'sequence' in cfg:
            seq = cfg['sequence']
            if isinstance(seq, list):
                for step in seq:
                    if isinstance(step, dict) and 'entity_id' in step.get('target', {}):
                        print(f'    -> updates: {step["target"]["entity_id"]}')
