import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

new_func = """def dps_string_list(dps_data: dict[str, dict], cloud_dp_codes: dict[str, dict]) -> list:
    \"\"\"Return list of friendly DPS values (v1.0.30 Robust).\"\"\"
    strs = []
    # v1.0.30 Fix: Prioritize discovered DPs and enrich with cloud data
    for dp, value in dps_data.items():
        dp_str = str(dp)
        label = f"{dp_str} (value: {value})"
        if dp_str in cloud_dp_codes:
            code = cloud_dp_codes[dp_str].get("code", "")
            if code: label = f"{dp_str} ( code: {code} , value: {value} )"
        strs.append(label)
    
    # Add cloud-only DPs
    discovered_keys = [str(k) for k in dps_data.keys()]
    for dp, func in cloud_dp_codes.items():
        if str(dp) not in discovered_keys:
            code = func.get("code", "cloud")
            strs.append(f"{dp} ( code: {code} , cloud pull )")
            
    return sorted(strs, key=lambda i: int(i.split()[0]))"""

import re
# Cerchiamo la funzione originale e sostituiamola interamente
pattern = re.compile(r'def dps_string_list\(.*?return sorted\(strs, key=lambda i: int\(i\.split\(\)\[0\]\)\)', re.DOTALL)

if pattern.search(content):
    updated_content = pattern.sub(new_func, content)
    with open(file_path, 'w') as f:
        f.write(updated_content)
    print("SUCCESS")
else:
    print("ERROR: Match failed")
