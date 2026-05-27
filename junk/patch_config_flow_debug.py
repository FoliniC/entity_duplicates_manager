import os
import re

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Cerchiamo il punto in cui LocalTuya recupera i DP dal cloud
old_cloud_logic = """    # Get DP descriptions from the cloud, if the device is there.
    cloud_dp_codes = {}
    cloud_data = entry_runtime.cloud_data
    if (dev_id := data.get(CONF_DEVICE_ID)) in cloud_data.device_list:
        cloud_dp_codes = await cloud_data.async_get_device_functions(dev_id)"""

new_cloud_logic = """    # v1.0.32 - Ultra Debug Cloud DP Mapping
    cloud_dp_codes = {}
    cloud_data = entry_runtime.cloud_data
    dev_id = data.get(CONF_DEVICE_ID)
    
    _LOGGER.info(f"[CL-DEBUG] Checking cloud data for device {dev_id}")
    
    if dev_id in cloud_data.device_list:
        _LOGGER.info(f"[CL-DEBUG] Device {dev_id} FOUND in cloud device list")
        cloud_dp_codes = await cloud_data.async_get_device_functions(dev_id)
        _LOGGER.info(f"[CL-DEBUG] cloud_dp_codes result: {cloud_dp_codes}")
    else:
        _LOGGER.warning(f"[CL-DEBUG] Device {dev_id} NOT FOUND in cloud list. Available: {list(cloud_data.device_list.keys())}")"""

if old_cloud_logic in content:
    updated_content = content.replace(old_cloud_logic, new_cloud_logic)
    with open(file_path, 'w') as f:
        f.write(updated_content)
    print("SUCCESS: Config Flow patched with Cloud Debug Logs.")
else:
    print("ERROR: Could not find cloud logic block in config_flow.py.")
