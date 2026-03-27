import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

merging_logic = """    # v1.0.33 - Merge Cloud DPs into detected_dps
    _LOGGER.info(f"[CL-DEBUG] Merging {len(cloud_dp_codes)} cloud DPs into detected list")
    for cloud_dp in cloud_dp_codes:
        if str(cloud_dp) not in detected_dps:
            detected_dps[str(cloud_dp)] = -1
"""

target_log = 'logger.info("Total DPS detected: %s", detected_dps)'

if target_log in content:
    updated_content = content.replace(target_log, merging_logic + "\n    " + target_log)
    with open(file_path, 'w') as f:
        f.write(updated_content)
    print("SUCCESS")
else:
    print("ERROR")
