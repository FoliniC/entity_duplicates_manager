import os

file_path = "/config/custom_components/localtuya/coordinator.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
in_initial_state_block = False
patch_applied = False

for i in range(len(lines)):
    line = lines[i]
    
    if 'self.debug("Retrieving initial state")' in line and not patch_applied:
        in_initial_state_block = True
        indent = line[:line.find("self.debug")]
        new_lines.append(indent + 'self.debug("Retrieving initial state (v1.0.26 - Ultra Wake-up)")\n')
        new_lines.append(indent + 'try:\n')
        new_lines.append(indent + '    await self._interface.heartbeat()\n')
        new_lines.append(indent + '    await asyncio.sleep(0.5)\n')
        new_lines.append(indent + '    await self._interface.update_dps()\n')
        new_lines.append(indent + '    await asyncio.sleep(0.5)\n')
        new_lines.append(indent + '    status = await self._interface.detect_available_dps(cid=self._node_id)\n')
        new_lines.append(indent + '    if not status:\n')
        new_lines.append(indent + '        status = await self._interface.status(cid=self._node_id)\n')
        new_lines.append(indent + 'except Exception as e:\n')
        new_lines.append(indent + '    self.warning(f"Wake-up failed for {host}: {e}")\n')
        new_lines.append(indent + '    status = {}\n')
        patch_applied = True
        continue

    if in_initial_state_block:
        if 'self.status_updated(status)' in line:
            in_initial_state_block = False
            new_lines.append(line)
        continue
    
    new_lines.append(line)

if patch_applied:
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    print("SUCCESS: Coordinator patched with clean indentation.")
else:
    print("ERROR: Injection point not found.")
