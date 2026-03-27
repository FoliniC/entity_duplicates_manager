import os

file_path = "/config/custom_components/localtuya/core/pytuya/__init__.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
patch_applied = False

for line in lines:
    if 'if self.dev_type == "type_0a" and not cid:' in line:
        indent = line[:line.find("if")]
        new_lines.append(indent + "# v1.0.28 Fix: Force full DP scan for all device types\n")
        new_lines.append(indent + "# " + line.lstrip())
        patch_applied = True
        continue
    
    if patch_applied and 'return self.dps_cache.get("parent", {})' in line:
        indent = line[:line.find("return")]
        new_lines.append(indent + "# " + line.lstrip())
        patch_applied = False
        continue

    new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("SUCCESS: pytuya patched.")
