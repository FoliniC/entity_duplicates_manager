import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Cerchiamo il punto prima del return finale in validate_input
target_log = 'logger.info("Total DPS detected: %s", detected_dps)'

robust_logging = """    # v1.0.34 - Explicit Local Discovery Logging
    local_count = len([k for k, v in detected_dps.items() if v != -1])
    cloud_count = len([k for k, v in detected_dps.items() if v == -1])
    _LOGGER.info(f"[CL-DEBUG] DISCOVERY SUMMARY: {local_count} DPs found locally, {cloud_count} DPs added from cloud. Total: {len(detected_dps)}")
    
    logger.info("Total DPS detected: %s", detected_dps)"""

if target_log in content:
    updated_content = content.replace(target_log, robust_logging)
    with open(file_path, 'w') as f:
        f.write(updated_content)
    print("SUCCESS: Config Flow patched with explicit summary logging.")
else:
    print("ERROR: Target log line not found.")
