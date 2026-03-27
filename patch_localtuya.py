import os

file_path = "/config/custom_components/localtuya/core/pytuya/__init__.py"
backup_path = "/config/custom_components/localtuya/core/pytuya/__init__.py.bak"

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
patch_applied = False

for i in range(len(lines)):
    line = lines[i]
    new_lines.append(line)
    if "if not await self._negotiate_session_key():" in line and not patch_applied:
        if i + 1 < len(lines) and "return self.clean_up_session()" in lines[i+1]:
            # Found the block!
            pass
    if len(new_lines) >= 2 and "if not await self._negotiate_session_key():" in new_lines[-2] and "return self.clean_up_session()" in new_lines[-1] and not patch_applied:
        indent = line[:line.find("return")]
        new_lines.append(indent + "# v1.0.23 Fix: Force status update to warm up session\n")
        new_lines.append(indent + "await self.detect_available_dps()\n")
        patch_applied = True

if patch_applied:
    if not os.path.exists(backup_path):
        os.rename(file_path, backup_path)
    with open(file_path, 'w') as f:
        f.writelines(new_lines)
    print("SUCCESS: LocalTuya patched with session warm-up logic.")
else:
    print("ERROR: Could not find the injection point in pytuya/__init__.py")
