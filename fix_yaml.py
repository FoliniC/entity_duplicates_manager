import os
import glob

for f in glob.glob("yaml_generator/template_triggers/*.yaml"):
    with open(f, 'r') as file:
        lines = file.readlines()
    
    new_lines = []
    # Inizia il blocco trigger
    new_lines.append("- trigger:\n")
    
    # Processa il resto
    in_sensor_block = False
    for line in lines:
        if "sensor:" in line:
            new_lines.append("\n- sensor:\n")
            in_sensor_block = True
            continue
        if in_sensor_block:
            new_lines.append(line)
        elif "trigger:" not in line and "- trigger:" not in line:
            new_lines.append("    " + line)
            
    with open(f, 'w') as file:
        file.writelines(new_lines)

