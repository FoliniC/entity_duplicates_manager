
entities = [
    "climate.controllo_temperatura_cucina",
    "climate.climatizzazione_appartamento",
    "sensor.fancoil_cucina_hvac_temp_mode",
    "input_select.fancoil_system_hvac_mode",
    "input_number.master_setpoint_heat",
    "input_number.master_setpoint_cool",
    "input_number.fancoil_cucina_sp_offset",
    "input_number.fancoil_cucina_setpoint",
    "input_boolean.fancoil_cucina_sp_follow_master",
    "input_select.hvac_profile",
    "switch.stox_fancoil_cucina_switch"
]

print("--- ENTITY STATES DUMP ---")
for e in entities:
    state = hass.states.get(e)
    if state:
        print(f"{e}: {state.state}")
        if state.attributes:
            print(f"  attrs: {state.attributes}")
    else:
        print(f"{e}: NOT FOUND")
