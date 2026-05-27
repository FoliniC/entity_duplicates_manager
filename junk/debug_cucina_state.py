
entity_ids = [
    "climate.controllo_temperatura_cucina",
    "climate.climatizzazione_appartamento",
    "input_boolean.fancoil_cucina_sp_follow_master",
    "input_select.fancoil_system_hvac_mode",
    "input_number.master_setpoint_heat",
    "input_number.master_setpoint_cool",
    "input_number.fancoil_cucina_sp_offset",
    "input_number.fancoil_cucina_setpoint",
    "input_boolean.fancoil_cucina_hvac_mode_follow_master",
    "input_select.fancoil_cucina_hvac_mode_local",
    "sensor.fancoil_cucina_last_temperature",
    "sensor.temperatura_cucina_reale_calcolata"
]

for entity_id in entity_ids:
    state = hass.states.get(entity_id)
    if state:
        print(f"{entity_id}: {state.state}")
        if entity_id.startswith("climate."):
            print(f"  attributes: {state.attributes}")
    else:
        print(f"{entity_id}: NOT FOUND")
