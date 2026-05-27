import os
import shutil
import re

CONFIG_DIR = "/home/carlo/docker/homeassistant/config"
JUNK_DIR = os.path.join(CONFIG_DIR, "junk")

# Root files to move:
ROOT_JUNK_FILES = [
    "clean_patch.py",
    "finalize_patch.py",
    "add_smart_meter_to_config.py",
    "check_current_state.py",
    "check_ev_sensors.py",
    "config_flow_tmp.py",
    "dump_all_states.py",
    "hass_unpacker.py",
    "process_adguard.py",
    "remove_blocker.py",
    "robust_connection.py",
    "tuya_client.py",
    "tuya_gui.py",
    "ms-python.vscode-pylance-2023.11.13_ok.vsix",
    "it_tmp.json",
    "manifest_tmp.json",
    "strings_tmp.json",
    "entities.txt",
    "commits.txt",
    "remove_large_files.txt",
    "tuya_manager_debug.log",
    "configuration copy.yaml",
]

# Root folder files pattern rules:
ROOT_JUNK_PATTERNS = [
    r"^debug_.*\.py$",
    r"^test_.*\.py$",
    r"^test_.*\.yaml$",
    r"^patch_.*\.py$",
    r"^fix_.*\.py$",
    r"^configuration\.yaml\..*$",
    r"^configuration_prev\.yaml$",
    r"^fan_coil_config\.yaml\.ko$",
]

# Generic patterns in all subdirectories (excluding junk/ itself)
GENERIC_JUNK_PATTERNS = [
    r"^.*\.py\.old$",
    r"^.*\.yaml\.old$",
    r"^.*\.yaml\.bak$",
    r"^.*\.yaml\.save$",
    r"^.*\.yaml\.save\.\d+$",
    r"^.*\.py_$",
    r"^.*\.py\.ok$",
    r"^.*\.lnk$",
]

# Specific directories to move:
JUNK_DIRECTORIES = [
    "custom_components/temp",
]

# Specific individual files to move in subdirectories:
SPECIFIC_JUNK_FILES = [
    "custom_components/entity_duplicates_manager/www/entity_duplicates_manager_card/entity-duplicates-manager-card.js.new",
    "custom_components/entity_duplicates_manager/www/entity_duplicates_manager_card/entity-duplicates-manager-card.js.old",
    "python_scripts/pyscript.toml",  # duplicate leftover
]

def should_move_root_file(filename):
    if filename in ROOT_JUNK_FILES:
        return True
    for pattern in ROOT_JUNK_PATTERNS:
        if re.match(pattern, filename):
            return True
    return False

def should_move_generic_file(filename):
    for pattern in GENERIC_JUNK_PATTERNS:
        if re.match(pattern, filename):
            return True
    return False

def move_path(relative_path):
    src = os.path.join(CONFIG_DIR, relative_path)
    if not os.path.exists(src):
        return
    dst = os.path.join(JUNK_DIR, relative_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print(f"Moving {relative_path} -> junk/{relative_path}")
    try:
        shutil.move(src, dst)
    except Exception as e:
        print(f"Error moving {relative_path}: {e}")

def main():
    # 1. Specific directories
    for rdir in JUNK_DIRECTORIES:
        src = os.path.join(CONFIG_DIR, rdir)
        if os.path.exists(src) and os.path.isdir(src):
            move_path(rdir)
            
    # 2. Specific files in subdirectories
    for rfile in SPECIFIC_JUNK_FILES:
        move_path(rfile)

    # 3. Walk directory tree
    for root, dirs, files in os.walk(CONFIG_DIR):
        # Skip the junk directory itself and hidden directories (like .git, .storage, etc.)
        if JUNK_DIR in root or any(d.startswith('.') for d in root.split(os.sep)):
            continue
            
        rel_dir = os.path.relpath(root, CONFIG_DIR)
        
        # Determine if we are at root
        is_root = (rel_dir == ".")
        
        for file in files:
            rel_file = os.path.join(rel_dir, file) if not is_root else file
            
            # Check root patterns
            if is_root:
                if should_move_root_file(file):
                    move_path(rel_file)
            else:
                # Check generic patterns in subdirectories
                if should_move_generic_file(file):
                    move_path(rel_file)

if __name__ == "__main__":
    main()
