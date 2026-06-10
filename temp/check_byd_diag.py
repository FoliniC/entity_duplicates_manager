# Diagnostic script to check BYD SOC and threshold values
print("--- BYD Protection Diagnostic ---")
print(f"BYD SOC: {state.get('sensor.byd_battery_box_premium_hv_state_of_charge')}")
print(f"Min SOC Threshold (p_min_stop): {state.get('input_number.ev_charge_2025_byd_min_soc_stop')}")
print(f"Automation target_amp calculation triggered")
