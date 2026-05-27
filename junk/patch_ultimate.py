import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# MODIFICA: Intercettiamo il punto esatto del return finale di validate_input
# e forziamo la restituzione di TUTTI i DP senza se e senza ma.

old_return_pattern = """    return {
        CONF_DPS_STRINGS: dps_string_list(detected_dps, cloud_dp_codes),
        CONF_PROTOCOL_VERSION: conf_protocol,
    }"""

new_forced_return = """    # v1.0.35 - Ultimate forced return
    final_dps = dps_string_list(detected_dps, cloud_dp_codes)
    
    # Se è il garage, garantiamo che la lista ritornata sia completa
    if data.get("device_id") == "bf27acf38b97deb8d9ogjj":
        _LOGGER.error(f"[ULTIMATE-FIX] Forcing final DP list for Garage. Current count: {len(final_dps)}")
        # Se per qualche motivo dps_string_list ha fallito, ricostruiamo a mano
        known = [s.split(" ")[0] for s in final_dps]
        for dp in ["1", "2", "3", "4", "5", "6", "11", "12"]:
            if dp not in known:
                final_dps.append(f"{dp} ( forced )")
        final_dps = sorted(final_dps, key=lambda i: int(i.split()[0]))

    return {
        CONF_DPS_STRINGS: final_dps,
        CONF_PROTOCOL_VERSION: conf_protocol,
    }"""

if old_return_pattern in content:
    updated = content.replace(old_return_pattern, new_forced_return)
    with open(file_path, 'w') as f:
        f.write(updated)
    print("SUCCESS: Ultimate return patch applied.")
else:
    # Provo a cercare solo una parte se la patch precedente ha cambiato qualcosa
    if "CONF_DPS_STRINGS: dps_string_list(detected_dps, cloud_dp_codes)" in content:
        import re
        # Sostituzione via regex più flessibile
        pattern = re.compile(r'return \{.*?CONF_DPS_STRINGS: dps_string_list\(detected_dps, cloud_dp_codes\),.*?\}', re.DOTALL)
        if pattern.search(content):
            updated = pattern.sub(new_forced_return, content)
            with open(file_path, 'w') as f:
                f.write(updated)
            print("SUCCESS (via regex)")
        else:
            print("ERROR: Regex match failed")
    else:
        print("ERROR: Could not find return block.")
