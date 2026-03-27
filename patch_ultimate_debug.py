import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

target = '        _LOGGER.error(f"[ULTIMATE-FIX] Forcing final DP list for Garage. Current count: {len(final_dps)}")'
injection = target + '
        for item in final_dps: _LOGGER.error(f"[ULTIMATE-FIX] ITEM: {item}")'

if target in content:
    with open(file_path, 'w') as f:
        f.write(content.replace(target, injection))
    print("SUCCESS")
else:
    print("ERROR")
