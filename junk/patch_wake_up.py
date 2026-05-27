import os

file_path = "/config/custom_components/localtuya/coordinator.py"

with open(file_path, 'r') as f:
    content = f.read()

wake_up_logic = """                self.debug("Forcing Ultra-Wake-up sequence (Heartbeat + UpdateDPS + Probe)")
                try:
                    await self._interface.heartbeat()
                    await asyncio.sleep(0.5)
                    await self._interface.update_dps()
                    await asyncio.sleep(0.5)
                    status = await self._interface.detect_available_dps(cid=self._node_id)
                    if not status:
                        status = await self._interface.status(cid=self._node_id)
                except Exception as e:
                    self.warning(f"Wake-up failed for {host}: {e}")
                    status = {}"""

if 'self.debug("Retrieving initial state' in content:
    start_marker = 'self.debug("Retrieving initial state'
    end_marker = 'self.status_updated(status)'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + wake_up_logic + "\n\n                " + content[end_idx:]
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("SUCCESS: LocalTuya Coordinator patched with Ultra-Wake-up logic.")
    else:
        print("ERROR: Markers not found.")
else:
    print("ERROR: Injection point not found.")
