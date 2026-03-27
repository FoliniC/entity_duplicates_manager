import datetime

entity_ids = [
    "climate.controllo_temperatura_cucina",
    "input_select.fancoil_system_hvac_mode",
    "input_boolean.fancoil_cucina_sp_follow_master",
    "input_number.master_setpoint_heat"
]

print("--- DETAILED STATE INSPECTION ---")
for entity_id in entity_ids:
    state = hass.states.get(entity_id)
    if state:
        print(f"Entity: {entity_id}")
        print(f"  State: '{state.state}'")
        print(f"  Attributes: {state.attributes}")
        print(f"  Last Changed: {state.last_changed}")
        print(f"  Last Updated: {state.last_updated}")
        print("-" * 20)
    else:
        print(f"Entity: {entity_id} NOT FOUND")

print("\n--- ALL CLIMATE ENTITIES ---")
climates = [s.entity_id for s in hass.states.all() if s.entity_id.startswith("climate.")]
for c in climates:
    print(c)
