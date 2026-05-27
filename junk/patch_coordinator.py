import os

file_path = "/config/custom_components/localtuya/coordinator.py"
backup_path = "/config/custom_components/localtuya/coordinator.py.bak"

with open(file_path, 'r') as f:
    content = f.read()

# Logic: replace the initial status query with a more robust one that tries detect_available_dps if status fails or is empty.
old_block = """                self.debug("Retrieving initial state")
                if int(self._device_config.scan_interval) == 0:
                    self.debug("Skipping initial status query for passive device")
                    status = {}
                else:
                    try:
                        status = await self._interface.status(cid=self._node_id)
                    except Exception as e:
                        self.warning(f"Initial status query failed ({e}), continuing in passive mode")
                        status = {}"""

new_block = """                self.debug("Retrieving initial state (forced robust query)")
                if int(self._device_config.scan_interval) == 0:
                    self.debug("Skipping initial status query for passive device")
                    status = {}
                else:
                    try:
                        # Try standard status first
                        status = await self._interface.status(cid=self._node_id)
                        # If empty or failed, try the more robust detect_available_dps
                        if not status:
                            self.debug("Initial status empty, trying robust DP probe")
                            status = await self._interface.detect_available_dps(cid=self._node_id)
                    except Exception as e:
                        self.debug(f"Initial status failed ({e}), trying robust DP probe as fallback")
                        try:
                            status = await self._interface.detect_available_dps(cid=self._node_id)
                        except Exception as e2:
                            self.warning(f"Forced DP probe also failed ({e2}), continuing in passive mode")
                            status = {}"""

if old_block in content:
    if not os.path.exists(backup_path):
        os.rename(file_path, backup_path)
    with open(file_path, 'w') as f:
        f.write(content.replace(old_block, new_block))
    print("SUCCESS: LocalTuya Coordinator patched for robust initial state retrieval.")
else:
    # Try a slightly different match if spacing differs
    print("ERROR: Could not find the exact code block in coordinator.py. Check for version differences.")
