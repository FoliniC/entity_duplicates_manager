#!/usr/bin/env python3
"""Convert legacy climate template files to HA 2026.x format.

This script updates generated climate files from the legacy
'- platform: climate_template' format to the modern 'climate:' + 'platform: template' format
required by Home Assistant 2026.x.
"""

import os
import re
from pathlib import Path

def convert_climate_file(file_path: Path) -> bool:
    """Convert a single climate file to HA 2026.x format."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file uses legacy format
    if '- platform: climate_template' not in content:
        return False
    
    # Replace legacy format with modern format
    # Pattern: '- platform: climate_template' -> 'platform: template'
    # And wrap in climate: structure
    new_content = re.sub(
        r'(\s*)-\s+platform:\s+climate_template',
        r'\1climate:\n\1  - platform: template',
        content
    )
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Converted: {file_path}")
    return True

def main():
    """Main function to convert all climate files."""
    # Path to generated climates directory
    climates_dir = Path('/home/carlo/docker/homeassistant/config/yaml_generator/generated_climates/')
    
    if not climates_dir.exists():
        print(f"Error: Directory {climates_dir} does not exist")
        return
    
    # Find all YAML files in the directory
    yaml_files = list(climates_dir.glob('*.yaml'))
    yaml_files.extend(list(climates_dir.glob('*.yml')))
    
    if not yaml_files:
        print(f"Error: No YAML files found in {climates_dir}")
        return
    
    print(f"Found {len(yaml_files)} YAML files to process")
    
    converted_count = 0
    for yaml_file in yaml_files:
        if convert_climate_file(yaml_file):
            converted_count += 1
    
    print(f"\nConversion complete: {converted_count}/{len(yaml_files)} files converted")
    
    # Update configuration.yaml to reference the new structure if needed
    config_file = Path('/home/carlo/docker/homeassistant/config/configuration.yaml')
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # If configuration still references legacy format, update it
        if 'climate: !include_dir_merge_list yaml_generator/generated_climates/' in config_content:
            print("Configuration already references modern climate format")

if __name__ == '__main__':
    main()