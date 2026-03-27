import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Cerchiamo il punto finale dove vengono restituiti i DP alla UI di HA
old_return = """    logger.info("Total DPS: %s", detected_dps)
    return {
        CONF_DPS_STRINGS: dps_string_list(detected_dps, cloud_dp_codes),
        CONF_PROTOCOL_VERSION: conf_protocol,
    }"""

# Inseriamo un blocco di iniezione forzata per il Garage Door
new_return = """    logger.info("Total DPS detected: %s", detected_dps)
    
    # v1.0.29 Fix: Forziamo l'inclusione dei DP conosciuti per il Garage se la scoperta fallisce
    if data.get(CONF_DEVICE_ID) == "bf27acf38b97deb8d9ogjj":
        for dp in ["1", "2", "3", "4", "5", "12"]:
            if dp not in detected_dps:
                detected_dps[dp] = -1
        logger.info("Forced DP injection for Garage: %s", detected_dps)

    return {
        CONF_DPS_STRINGS: dps_string_list(detected_dps, cloud_dp_codes),
        CONF_PROTOCOL_VERSION: conf_protocol,
    }"""

if old_return in content:
    with open(file_path, 'w') as f:
        f.write(content.replace(old_return, new_return))
    print("SUCCESS: Config Flow patched with Forced DP Injection.")
else:
    print("ERROR: Return block not found in config_flow.py.")
