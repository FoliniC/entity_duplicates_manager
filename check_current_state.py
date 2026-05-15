
entities = [
    "input_select.fancoil_system_hvac_mode",
    "schedule.riscaldamento",
    "switch.attiva_pdc",
    "switch.attiva_fancoil",
    "sensor.temperatura_circuito_riscaldamento",
    "binary_sensor.fancoil_circuit_temp_invalid",
    "climate.controllo_temperatura_cucina",
    "sensor.fancoil_cucina_hvac_temp_mode",
    "sensor.fancoil_cucina_temperature_difference",
    "sensor.temperatura_cucina_reale_calcolata",
    "sensor.th1a_temperature"
]

print("--- CURRENT STATES ---")
for e in entities:
    state = hass.states.get(e)
    if state:
        print(f"{e}: {state.state}")
        if state.attributes:
             # Just print some attributes
             for attr in ['temperature', 'current_temperature', 'hvac_mode', 'hvac_modes']:
                 if attr in state.attributes:
                     print(f"  {attr}: {state.attributes[attr]}")
    else:
        print(f"{e}: NOT FOUND")
