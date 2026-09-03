import json, os, sqlite3

db_dir = '/config/.storage/'
reg_file = os.path.join(db_dir, 'core.entity_registry')

if os.path.exists(reg_file):
    d = json.load(open(reg_file))
    print("=== BTC/Phone entities in registry ===")
    for e in d['data']['entities']:
        eid = e['entity_id']
        if any(k in eid.lower() for k in ['btc', 'bitcoin', 'phone']):
            print(f"  {eid}: name={e.get('original_name','?')}, disabled={e.get('disabled_by','?')}, state_class={e.get('state_class','?')}")

# Check for DB files
print("\n=== DB files in .storage ===")
for f in os.listdir(db_dir):
    if f.endswith('.db'):
        size = os.path.getsize(os.path.join(db_dir, f))
        print(f"  {f}: {size} bytes")

# Check recorder state
print("\n=== Recorder config ===")
rec_file = os.path.join(db_dir, 'recorder')
if os.path.exists(rec_file):
    print(open(rec_file).read()[:200])
else:
    # Try to find in configuration
    import glob
    for p in glob.glob('/config/*.yaml'):
        content = open(p).read()
        if 'recorder' in content.lower():
            print(f"Found recorder in {p}:")
            lines = content.split('\n')
            for i, l in enumerate(lines):
                if 'recorder' in l.lower():
                    print('\n'.join(lines[max(0,i-1):i+5]))
                    break
            break
