import os

file_path = "/config/custom_components/localtuya/core/cloud_api.py"
backup_path = "/config/custom_components/localtuya/core/cloud_api.py.bak_cloud"

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "as resp:" in line:
        indent = line[:line.find("async")]
        # Using string concatenation to avoid newline issues in f-strings
        new_lines.append(indent + "    self._logger.debug('CLOUD API RESP - Status: %s - Body: %s', resp.status, await resp.text())\n")

if not os.path.exists(backup_path):
    os.rename(file_path, backup_path)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("SUCCESS: Tuya Cloud API logging patched.")
