#!/usr/bin/env python3
"""
HermesCatalogPatch.py — Configura modelli e provider Azure Foundry su Hermes Agent.

Uso:
  python3 HermesCatalogPatch.py models slug1 slug2 ...   # aggiunge modelli OpenRouter
  python3 HermesCatalogPatch.py azure-foundry --base-url URL --model NAME  # configura azure-foundry
  python3 HermesCatalogPatch.py all  # esegue entrambi

Caratteristiche:
  1. Patch config.yaml per model_catalog locale
  2. Aggiunge modelli OpenRouter a openrouter/__init__.py e hermes_cli/models.py
  3. Configura provider azure-foundry in config.yaml con base_url e api_mode
  4. Patcha i file Python per aggiungere alias azure-foundry (model_normalize.py, models.py, auth.py)
  5. Imposta AZURE_FOUNDRY_API_KEY nel .env
  6. Rimuove cache e ricostruisce il catalogo modelli
"""
import os
import sys
import shutil
import argparse
import pathlib
import subprocess
import re


def get_hermes_dir():
    """Detect the Hermes installation directory."""
    if sys.platform == "win32":
        appdata = os.environ.get(
            "LOCALAPPDATA",
            os.path.join(os.path.expanduser("~"), "AppData", "Local"),
        )
        hermes_dir = os.path.join(appdata, "hermes")
        if os.path.exists(hermes_dir):
            return hermes_dir
    return os.path.expanduser("~/.hermes")


def backup_file(path):
    """Create a backup of the file before modifying it."""
    if os.path.exists(path):
        backup_path = path + ".script_backup"
        shutil.copy2(path, backup_path)
        print(f"[*] Backed up: {os.path.basename(path)}")


# ---------------------------------------------------------------------------
# Config YAML / model_catalog
# ---------------------------------------------------------------------------

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

    catalog_json_path = os.path.join(agent_dir, "website", "static", "api", "model-catalog.json")
    file_uri = pathlib.Path(catalog_json_path).as_uri()

    catalog_config = (
        "model_catalog:\n"
        "  enabled: true\n"
        f'  url: "{file_uri}"\n'
        "  ttl_hours: 168\n"
    )

    backup_file(config_path)
    if "providers:" in content:
        content = content.replace("providers:", catalog_config + "providers:", 1)
    else:
        content += "\n" + catalog_config

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Patched config.yaml")


# ---------------------------------------------------------------------------
# OpenRouter model registration
# ---------------------------------------------------------------------------

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
        print("[+] Patched openrouter/__init__.py")
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

    cache_var = "_openrouter_catalog_cache:"
    if cache_var not in content:
        print(f"[-] Could not find '{cache_var}' in models.py")
        return

    parts = content.split(cache_var)
    idx = parts[0].rfind("]")
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
        print("[+] Patched hermes_cli/models.py")
    else:
        print("[*] Models already present in models.py")


# ---------------------------------------------------------------------------
# Azure Foundry provider registration
# ---------------------------------------------------------------------------

def ensure_azure_provider_aliases(agent_dir):
    """Patch code files to add azure-foundry provider aliases."""

    # --- model_normalize.py ---
    normalize_path = os.path.join(agent_dir, "hermes_cli", "model_normalize.py")
    if os.path.exists(normalize_path):
        with open(normalize_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "azure-foundry" not in content:
            content = content.replace(
                '    "xai",\n})',
                '    "xai",\n    "azure-foundry",\n})',
                1,
            )
            backup_file(normalize_path)
            with open(normalize_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("[+] Added azure-foundry to model_normalize.py _MATCHING_PREFIX_STRIP_PROVIDERS")
        else:
            print("[*] azure-foundry already present in model_normalize.py")

    # --- models.py _PROVIDER_ALIASES ---
    models_path = os.path.join(agent_dir, "hermes_cli", "models.py")
    if os.path.exists(models_path):
        with open(models_path, "r", encoding="utf-8") as f:
            content = f.read()
        if '"azure-foundry": "azure-foundry"' not in content:
            content = content.replace(
                '"xai-grok-oauth": "xai-oauth",',
                '"xai-grok-oauth": "xai-oauth",\n    "azure": "azure-foundry",\n    "azure-foundry": "azure-foundry",\n    "azure-ai-foundry": "azure-foundry",',
                1,
            )
            backup_file(models_path)
            with open(models_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("[+] Added azure-foundry aliases to models.py _PROVIDER_ALIASES")
        else:
            print("[*] azure-foundry aliases already present in models.py")

    # --- auth.py resolve_provider() local alias dict ---
    auth_path = os.path.join(agent_dir, "hermes_cli", "auth.py")
    if os.path.exists(auth_path):
        with open(auth_path, "r", encoding="utf-8") as f:
            content = f.read()
        if '"azure-foundry": "azure-foundry"' not in content:
            content = content.replace(
                '"xai-grok-oauth": "xai-oauth",',
                '"xai-grok-oauth": "xai-oauth",\n        "azure": "azure-foundry", "azure-foundry": "azure-foundry", "azure-ai-foundry": "azure-foundry",',
                1,
            )
            backup_file(auth_path)
            with open(auth_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("[+] Added azure-foundry aliases to auth.py resolve_provider()")
        else:
            print("[*] azure-foundry aliases already present in auth.py")


def setup_azure_foundry_model(hermes_dir, base_url, model_name,
                              api_key_env_var="AZURE_FOUNDRY_API_KEY"):
    """Configure config.yaml with azure-foundry provider and model."""
    config_path = os.path.join(hermes_dir, "config.yaml")
    if not os.path.exists(config_path):
        print(f"[-] Config not found at {config_path}")
        return False

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    backup_file(config_path)

    # --- model section ---
    model_section = (
        "model:\n"
        f"  default: {model_name}\n"
        "  provider: azure-foundry\n"
        f"  base_url: {base_url}\n"
        "  api_mode: chat_completions\n"
    )

    if "model:" in content:
        model_start = content.find("model:")
        providers_start = content.find("providers:", model_start)
        if providers_start != -1:
            content = content[:model_start] + model_section + "\n" + content[providers_start:]
        else:
            # model block is last section — truncate after it
            rest_idx = model_start
            line_end = content.find("\n", rest_idx)
            content = content[:model_start] + model_section + "\n" + content[line_end + 1:]
    else:
        content += "\n" + model_section

    # --- providers section ---
    if "azure-foundry:" not in content:
        provider_entry = (
            "  azure-foundry:\n"
            f"    base_url: {base_url}\n"
            f"    api_key: ${{{api_key_env_var}}}\n"
            "    name: Azure Foundry\n"
            "    api_mode: chat_completions\n"
        )
        if "providers:" in content:
            content = content.replace("providers:", "providers:\n" + provider_entry, 1)
        else:
            content += "\nproviders:\n" + provider_entry
    else:
        # update existing block's base_url + api_key lines
        content = re.sub(
            r"^(azure-foundry:\s*\n(?:\s+\w+:.*\n)+)",
            lambda m: re.sub(
                r"^(    base_url: ).*$",
                f"\\g<1>{base_url}",
                m.group(0),
                flags=re.MULTILINE,
            ),
            content,
            flags=re.MULTILINE,
        )

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[+] Configured config.yaml with azure-foundry/{model_name}")

    # --- .env ---
    env_path = os.path.join(hermes_dir, ".env")
    env_line = f"{api_key_env_var}='***"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write(env_line + "\n")
    else:
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()
        if api_key_env_var not in env_content:
            env_content += "\n" + env_line + "\n"
        else:
            env_content = re.sub(
                rf"^{api_key_env_var}=[^\n]*",
                env_line,
                env_content,
                flags=re.MULTILINE,
            )
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        print(f"[+] Set {api_key_env_var} in .env (placeholder — replace with real key)")

    return True


# ---------------------------------------------------------------------------
# Catalog rebuild / cache clear
# ---------------------------------------------------------------------------

def rebuild_catalog_and_clear_cache(hermes_dir, agent_dir):
    """Run the build script and purge hermes caches."""
    script_path = os.path.join(agent_dir, "scripts", "build_model_catalog.py")
    if os.path.exists(script_path):
        print("[*] Rebuilding model catalog...")
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
        os.path.join(hermes_dir, "provider_models_cache.json"),
    ]
    for cache_file in caches_to_remove:
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"[+] Removed cache: {os.path.basename(cache_file)}")
            except Exception as e:
                print(f"[-] Failed to remove {cache_file}: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Configure Hermes local catalog, OpenRouter models, and Azure Foundry provider.",
    )
    sub = parser.add_subparsers(dest="command", help="Action to perform")

    # `models` subcommand — original behaviour
    p_models = sub.add_parser("models", help="Add OpenRouter model slugs to Hermes")
    p_models.add_argument("slugs", nargs="*", help="Model slugs, e.g. poolside/laguna-s-2.1:free")

    # `azure-foundry` subcommand
    p_az = sub.add_parser("azure-foundry", help="Configure the Azure Foundry provider + model")
    p_az.add_argument("--base-url", required=True, help="Azure Foundry OpenAI v1 endpoint URL")
    p_az.add_argument("--model", required=True, help="Deployment name (e.g. gpt-5.6-terra)")
    p_az.add_argument("--env-var", default="AZURE_FOUNDRY_API_KEY", help="Env var name for the API key (default: AZURE_FOUNDRY_API_KEY)")

    # `all` subcommand — do everything
    p_all = sub.add_parser("all", help="Patch code, config, and catalog for both OR and azure-foundry")
    p_all.add_argument("slugs", nargs="*", help="OpenRouter slugs to add")
    p_all.add_argument("--base-url", required=True, help="Azure Foundry OpenAI v1 endpoint URL")
    p_all.add_argument("--model", required=True, help="Azure Foundry deployment name")

    # bare args — default to the old behaviour (OpenRouter models)
    parser.add_argument("bare_slugs", nargs="*", help="Model slugs (OpenRouter) — same as `models`")

    args = parser.parse_args()

    hermes_dir = get_hermes_dir()
    agent_dir = os.path.join(hermes_dir, "hermes-agent")

    if not os.path.exists(hermes_dir) or not os.path.exists(agent_dir):
        print(f"[-] Hermes directory not found. Looked in: {hermes_dir}")
        sys.exit(1)

    print(f"[*] Hermes config dir: {hermes_dir}")
    print(f"[*] Hermes agent dir:  {agent_dir}")

    # If no subcommand given, treat bare args as OpenRouter models
    cmd = args.command or ("models" if (args.bare_slugs or True) else None)
    slugs = args.bare_slugs if args.command is None else getattr(args, "slugs", [])

    if cmd == "all":
        patch_config(hermes_dir, agent_dir)
        patch_openrouter_init(agent_dir, slugs)
        patch_models_py(agent_dir, slugs)
        ensure_azure_provider_aliases(agent_dir)
        setup_azure_foundry_model(hermes_dir, args.base_url, args.model)
        rebuild_catalog_and_clear_cache(hermes_dir, agent_dir)
    elif cmd == "azure-foundry":
        ensure_azure_provider_aliases(agent_dir)
        setup_azure_foundry_model(hermes_dir, args.base_url, args.model, api_key_env_var=args.env_var)
        rebuild_catalog_and_clear_cache(hermes_dir, agent_dir)
    elif cmd == "models" or args.bare_slugs:
        patch_config(hermes_dir, agent_dir)
        patch_openrouter_init(agent_dir, slugs or args.bare_slugs)
        patch_models_py(agent_dir, slugs or args.bare_slugs)
        rebuild_catalog_and_clear_cache(hermes_dir, agent_dir)
    else:
        # default: just patch config + rebuild
        patch_config(hermes_dir, agent_dir)
        rebuild_catalog_and_clear_cache(hermes_dir, agent_dir)

    print("\n[+] Done!")


if __name__ == "__main__":
    main()
