import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# MODIFICA: Interveniamo su col_to_select per forzare la lista nella UI
old_col_to_select = """def col_to_select(
    opt_list: dict | list, multi_select=False, is_dps=False, custom_value=False
) -> SelectSelector:"""

new_col_to_select = """def col_to_select(
    opt_list: dict | list, multi_select=False, is_dps=False, custom_value=False
) -> SelectSelector:
    # v1.0.36 - UI Force Injection
    if is_dps and isinstance(opt_list, list) and len(opt_list) <= 1:
        # Se la UI sta cercando di mostrare solo 1 DP, aggiungiamo i forzati per il garage come emergenza
        # Nota: usiamo una lista statica dei DP del garage se siamo in questa condizione critica
        forced_garage = ["1 (switch_1)", "2 (countdown_1)", "3 (doorcontact_state)", "4 (door_time_1)", "5 (alarm_countdown_1)", "6 (door_control_1)", "11 (voice_control_1)", "12 (door_state_1)"]
        # Se il primo elemento sembra un DP del garage, facciamo il merge
        if opt_list and ("1 " in str(opt_list[0]) or "bf27acf3" in str(opt_list)):
             opt_list = sorted(list(set(opt_list + forced_garage)), key=lambda x: int(x.split(" ")[0]))
"""

if old_col_to_select in content:
    updated = content.replace(old_col_to_select, new_col_to_select)
    with open(file_path, 'w') as f:
        f.write(updated)
    print("SUCCESS: UI selector patched.")
else:
    print("ERROR: Could not find col_to_select.")
