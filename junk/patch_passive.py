import os

file_path = "/config/custom_components/localtuya/coordinator.py"

with open(file_path, 'r') as f:
    content = f.read()

new_robust_logic = """                self.debug("Retrieving initial state (forced robust query for all devices)")
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

if "Retrieving initial state" in content:
    start_marker = 'self.debug("Retrieving initial state'
    end_marker = 'self.status_updated(status)'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + new_robust_logic + "\n\n                " + content[end_idx:]
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("SUCCESS: LocalTuya Coordinator patched to force initial status even for passive devices.")
    else:
        print("ERROR: Could not locate start or end markers.")
else:
    print("ERROR: Could not find 'Retrieving initial state' in coordinator.py")
