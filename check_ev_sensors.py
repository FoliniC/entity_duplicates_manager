
import json

entities = [
    "sensor.smart_meter_ts_100a_1_potenza_reale",
    "sensor.prism_potenza_assorbita",
    "sensor.byd_battery_box_premium_hv_state_of_charge",
    "sensor.folini_carlo_voltage_ac",
    "sensor.envoy_122134037538_current_power_production",
    "sensor.ev_charge_2025_solar_max_ampere",
    "input_boolean.ev_charge_2025_charging_active",
    "input_select.ev_charge_2025_mode",
    "input_number.ev_charge_2025_cronostar_power_target",
    "sensor.potenza_prelevata_attuale",
    "sensor.byd_battery_box_premium_hv_current_dc",
    "sensor.byd_battery_box_premium_hv_voltage_dc"
]

# Note: This script is intended to be run in an environment where 'hass' is available, 
# like a Home Assistant python_script or a pyscript. 
# Since I am in a shell, I can't run this directly against HA unless I use the CLI or API.
# I will try to see if there's a way to get these from the command line.

# However, I can't easily run this. I'll check if there's a 'ha' command available.
