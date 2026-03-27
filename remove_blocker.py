import os

file_path = '/config/custom_components/localtuya/config_flow.py'
with open(file_path, 'r') as f:
    content = f.read()

# Completely remove the EmptyDpsList check to let the user proceed
old_code = """    if not detected_dps_device and not (
        (cloud_dp_codes or detected_dps) and bypass_handshake
    ):
        raise EmptyDpsList"""

new_code = """    if not detected_dps_device and not (
        (cloud_dp_codes or detected_dps) and bypass_handshake
    ):
        _LOGGER.warning("No DPS detected, but allowing registration as requested by user.")
        # We ensure detected_dps is not empty to avoid downstream crashes
        if not detected_dps:
            detected_dps = {"1": -1}"""

if old_code in content:
    new_content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(new_content)
    print("EmptyDpsList blocker REMOVED")
else:
    # Try with the already patched version
    old_patched = """    if not detected_dps_device and not (
        (cloud_dp_codes or detected_dps) and bypass_handshake
    ):
        if data.get("scan_interval") == 0 or data.get("device_sleep_time", 0) > 0:
             _LOGGER.info("Bypassing EmptyDpsList for passive/low-power device")
        else:
             raise EmptyDpsList"""
    
    if old_patched in content:
        new_content = content.replace(old_patched, new_code)
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("EmptyDpsList blocker REMOVED (from patched version)")
    else:
        print("Could not find code block to patch")
