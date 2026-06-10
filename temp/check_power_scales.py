# Checking power sensors for scale errors
import json

sensors = [
    "sensor.produzione_solare",
    "sensor.potenza_prelevata_attuale",
    "sensor.solarnet_power_battery_discharge",
    "sensor.potenza_consumata_attuale",
    "sensor.envoy_122134037538_current_power_production",
    "sensor.alfa_potenza_attiva_prelevata_istantanea",
    "sensor.alfa_potenza_attiva_prodotta_istantanea",
    "sensor.smart_meter_ts_100a_1_potenza_reale",
    "sensor.produzione_solare_combined"
]

print("--- Power Sensors Info ---")
# Since I can't query live HA API directly, I'll check core.restore_state
try:
    with open(".storage/core.restore_state", "r") as f:
        data = json.load(f)
        for s in sensors:
            for entry in data.get("data", []):
                if entry.get("state", {}).get("entity_id") == s:
                    st = entry["state"]
                    print(f"Entity: {s}")
                    print(f"  State: {st.get('state')}")
                    print(f"  Unit: {st.get('attributes', {}).get('unit_of_measurement')}")
                    print(f"  Friendly: {st.get('attributes', {}).get('friendly_name')}")
except Exception as e:
    print(f"Error reading restore_state: {e}")
