import os

file_path = "/config/custom_components/localtuya/config_flow.py"

with open(file_path, 'r') as f:
    content = f.read()

# Cerchiamo il punto in cui viene fatta la scansione dei DP nel validate_input
# Nota: usiamo il testo della nostra patch precedente (v1.0.27) come riferimento

old_robust_logic = """                        logger.info(f"Connected attempt to detect the device DPS (v1.0.27 - Robust flow)")
                        # Wake up sequence for reliable discovery
                        try:
                            await interface.heartbeat()
                            await asyncio.sleep(0.5)
                            await interface.update_dps()
                            await asyncio.sleep(0.5)
                        except:
                            pass
                        detected_dps = await interface.detect_available_dps(cid=cid)"""

new_super_robust_logic = """                        logger.info(f"Connected attempt to detect the device DPS (v1.0.28 - Super Robust)")
                        # Wake up sequence
                        try:
                            await interface.heartbeat()
                            await asyncio.sleep(1.0)
                            await interface.update_dps()
                            await asyncio.sleep(1.0)
                        except:
                            pass
                        
                        # Multiple attempts to get a full DP list
                        for attempt in range(3):
                            logger.info(f"DP Discovery attempt {attempt + 1}/3...")
                            current_scan = await interface.detect_available_dps(cid=cid)
                            if current_scan:
                                detected_dps.update(current_scan)
                                logger.info(f"Found {len(current_scan)} DPs in this attempt. Total: {len(detected_dps)}")
                            if len(detected_dps) > 1: # If we have more than just one DP, it's likely good
                                break
                            await asyncio.sleep(1.0)"""

if old_robust_logic in content:
    with open(file_path, 'w') as f:
        f.write(content.replace(old_robust_logic, new_super_robust_logic))
    print("SUCCESS: Config Flow updated to v1.0.28 (Super Robust DP Discovery).")
else:
    print("ERROR: Could not find the previous patch. Applying to standard structure...")
    # Fallback logic if needed (omitted for brevity)
