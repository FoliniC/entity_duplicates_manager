import json

with open('/config/.storage/emulated_hue.ids') as f:
    data = json.load(f)

# Entità STALE da rimuovere (template lights/switches che non esistono più)
stale_entities = {
    'light.uscita',           # 285
    'light.entrata',          # 286
    'light.ritorno_a_casa',   # 287
    'light.verifica',         # 288
    'switch.alexa_uscita',    # 289
    'switch.alexa_entrata',   # 290
    'switch.alexa_ritorno_a_casa',  # 291
    'switch.alexa_verifica',  # 292
}

original = data['data']
filtered = {k: v for k, v in original.items() if v not in stale_entities}

print(f"Prima: {len(original)} entità")
print(f"Dopo: {len(filtered)} entità")
print("Rimosse:")
for k, v in original.items():
    if v in stale_entities:
        print(f"  {k}: {v}")

data['data'] = filtered

with open('/config/.storage/emulated_hue.ids', 'w') as f:
    json.dump(data, f, indent=2)

print("Fatto!")