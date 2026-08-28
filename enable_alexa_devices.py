import json

# Load the config entries
with open('/config/.storage/core.config_entries', 'r') as f:
    data = json.load(f)

# Find and enable alexa_devices entry
for entry in data['data']['entries']:
    if entry['domain'] == 'alexa_devices':
        entry['disabled_by'] = None
        print(f"✅ Abilitato alexa_devices (entry_id: {entry['entry_id']})")
        break

# Write back
with open('/config/.storage/core.config_entries', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Configurazione aggiornata - alexa_devices riabilitato")