#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import pathlib
import subprocess

def get_hermes_dir():
    """Detect the Hermes installation directory."""
    if sys.platform == "win32":
        # Windows location (AppData/Local)
        appdata = os.environ.get("LOCALAPPDATA", os.path.join(os.path.expanduser("~"), "AppData", "Local"))
        hermes_dir = os.path.join(appdata, "hermes")
        if os.path.exists(hermes_dir):
            return hermes_dir
    
    # Fallback / Typical Unix location (~/.hermes)
    return os.path.expanduser("~/.hermes")

def backup_file(path):
    """Create a backup of the file before modifying it."""
    if os.path.exists(path):
        backup_path = path + ".script_backup"
        shutil.copy2(path, backup_path)
        print(f"[*] Backed up: {os.path.basename(path)}")

def patch_config(hermes_dir, agent_dir):
    """Add model_catalog to config.yaml if it's missing."""
    config_path = os.path.join(hermes_dir, "config.yaml")
    if not os.path.exists(config_path):
        print(f"[-] Config not found at {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "model_catalog:" in content:
        print("[*] model_catalog already configured in config.yaml")
        return

    # Convert the path to a valid file:/// URI
    catalog_json_path = os.path.join(agent_dir, "website", "static", "api", "model-catalog.json")
    file_uri = pathlib.Path(catalog_json_path).as_uri()

    catalog_config = f"""model_catalog:
  enabled: true
  url: "{file_uri}"
  ttl_hours: 168
"""
    
    backup_file(config_path)
    if "providers:" in content:
        content = content.replace("providers:", catalog_config + "providers:")
    else:
        content += "\n" + catalog_config

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Patched config.yaml")

def patch_openrouter_init(agent_dir, slugs):
    """Add models to openrouter/__init__.py fallback_models tuple."""
    if not slugs:
        return

    init_path = os.path.join(agent_dir, "plugins", "model-providers", "openrouter", "__init__.py")
    if not os.path.exists(init_path):
        print(f"[-] {init_path} not found")
        return

    with open(init_path, "r", encoding="utf-8") as f:
        content = f.read()

    anchor = "fallback_models=("
    if anchor not in content:
        print("[-] Could not find 'fallback_models=(' in openrouter/__init__.py")
        return

    start_idx = content.find(anchor) + len(anchor)
    end_idx = content.find(")", start_idx)
    
    existing_models = content[start_idx:end_idx]
    added = False
    
    insert_str = ""
    for slug in slugs:
        if f'"{slug}"' not in existing_models and f"'{slug}'" not in existing_models:
            insert_str += f'\n        "{slug}",'
            added = True

    if added:
        backup_file(init_path)
        new_content = content[:end_idx] + insert_str + "\n    " + content[end_idx:]
        with open(init_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[+] Patched openrouter/__init__.py")
    else:
        print("[*] Models already present in openrouter/__init__.py")

def patch_models_py(agent_dir, slugs):
    """Add models to hermes_cli/models.py OPENROUTER_MODELS list."""
    if not slugs:
        return

    models_path = os.path.join(agent_dir, "hermes_cli", "models.py")
    if not os.path.exists(models_path):
        print(f"[-] {models_path} not found")
        return

    with open(models_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The list is usually right before this variable declaration
    cache_var = "_openrouter_catalog_cache:"
    if cache_var not in content:
        print("[-] Could not find '_openrouter_catalog_cache:' in models.py")
        return

    parts = content.split(cache_var)
    idx = parts[0].rfind(']')
    
    if idx == -1:
        print("[-] Could not find the end of OPENROUTER_MODELS list")
        return

    added = False
    insert_str = ""
    for slug in slugs:
        if f'"{slug}"' not in parts[0] and f"'{slug}'" not in parts[0]:
            insert_str += f'    ("{slug}", "added via script"),\n'
            added = True

    if added:
        backup_file(models_path)
        parts[0] = parts[0][:idx] + insert_str + parts[0][idx:]
        new_content = cache_var.join(parts)
        with open(models_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"[+] Patched hermes_cli/models.py")
    else:
        print("[*] Models already present in models.py")

def rebuild_catalog_and_clear_cache(hermes_dir, agent_dir):
    """Run the build script and purge hermes caches."""
    print("[*] Rebuilding model catalog...")
    script_path = os.path.join(agent_dir, "scripts", "build_model_catalog.py")
    if os.path.exists(script_path):
        try:
            subprocess.run([sys.executable, script_path], cwd=agent_dir, check=True)
            print("[+] Catalog rebuilt successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[-] Failed to rebuild catalog: {e}")
    else:
        print(f"[-] Catalog build script not found at {script_path}")

    print("[*] Clearing caches...")
    caches_to_remove = [
        os.path.join(hermes_dir, "cache", "model_catalog.json"),
        os.path.join(hermes_dir, "provider_models_cache.json")
    ]
    
    for cache_file in caches_to_remove:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"[+] Removed cache: {os.path.basename(cache_file)}")
            except Exception as e:
                print(f"[-] Failed to remove {cache_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Configure Hermes local catalog and optionally add OpenRouter models.")
    # Changed nargs="+" to nargs="*" to make arguments optional
    parser.add_argument("models", nargs="*", help="Optional: One or more model slugs (e.g., poolside/laguna-s-2.1:free)")
    args = parser.parse_args()

    hermes_dir = get_hermes_dir()
    agent_dir = os.path.join(hermes_dir, "hermes-agent")

    if not os.path.exists(hermes_dir) or not os.path.exists(agent_dir):
        print(f"[-] Hermes directory not found. Looked in: {hermes_dir}")
        sys.exit(1)

    print(f"[*] Hermes config dir: {hermes_dir}")
    print(f"[*] Hermes agent dir:  {agent_dir}")
    
    if args.models:
        print(f"[*] Models to add: {', '.join(args.models)}\n")
    else:
        print("[*] No new models specified. Patching config and rebuilding existing catalog...\n")

    patch_config(hermes_dir, agent_dir)
    patch_openrouter_init(agent_dir, args.models)
    patch_models_py(agent_dir, args.models)
    rebuild_catalog_and_clear_cache(hermes_dir, agent_dir)

    print("\n[+] All done!")

if __name__ == "__main__":
    main()