"""The Entity Duplicates Manager integration."""

import logging
from pathlib import Path

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration
from homeassistant.components.frontend import add_extra_js_url

try:
    from homeassistant.components.http import StaticPathConfig
    HAS_STATIC_PATH_CONFIG = True
except ImportError:
    HAS_STATIC_PATH_CONFIG = False

from .const import DOMAIN, SERVICE_SCAN, SERVICE_FIX, SERVICE_DELETE
from .scanner import DuplicatesScanner
from .storage import StorageManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["number", "text", "switch", "sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Entity Duplicates Manager from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    
    storage = StorageManager(hass)
    await storage.async_load()
    hass.data[DOMAIN]["storage"] = storage

    # Register static resources for Lovelace card
    await _setup_static_resources(hass)

    scanner = DuplicatesScanner(hass)
    hass.data[DOMAIN]["scanner"] = scanner

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_scan(call: ServiceCall):
        """Handle the scan service."""
        # limit can be None (from empty textbox) or an int
        limit = call.data.get("max_suffix")
        exclude_str = call.data.get("exclusion_patterns")
        
        stored_config = storage.config
        
        # If parameters are missing from call, check storage
        # But if they are present and null/empty, we respect that
        if "max_suffix" not in call.data:
            limit = stored_config.get("max_suffix", 9)
        
        if "exclusion_patterns" not in call.data:
            exclude_str = stored_config.get("exclusion_patterns", "")
        
        # Save last used settings to storage (limit might be None here)
        await storage.async_save({
            "max_suffix": int(limit) if limit is not None and str(limit).strip() != "" else None,
            "exclusion_patterns": exclude_str
        })

        exclude_list = [p.strip() for p in exclude_str.split(",") if p.strip()] if exclude_str else []
        excluded_entities = storage.config.get("excluded_entities", [])
        
        _LOGGER.info(f"Scanning with limit={limit}, patterns={exclude_list}, excluded={excluded_entities}")
        
        results = scanner.scan(int(limit) if limit is not None and str(limit).strip() != "" else None, exclude_list)
        
        filtered_results = [d for d in results if d["entity_id"] not in excluded_entities]
        scanner._duplicates = filtered_results
        
        hass.bus.async_fire(f"{DOMAIN}_scan_complete", {
            "duplicates": filtered_results,
            "config": storage.config
        })

    async def handle_save_settings(call: ServiceCall):
        """Save settings without scanning."""
        limit = call.data.get("max_suffix")
        await storage.async_save({
            "max_suffix": int(limit) if limit is not None and str(limit).strip() != "" else None,
            "exclusion_patterns": call.data.get("exclusion_patterns", "")
        })

    async def handle_exclude_entities(call: ServiceCall):
        """Add entities to exclusion list."""
        entity_ids = call.data.get("entity_ids", [])
        current = storage.config.get("excluded_entities", [])
        new_list = list(set(current + entity_ids))
        await storage.async_save({"excluded_entities": new_list})
        _LOGGER.info(f"Entities added to exclusions: {entity_ids}")
        # Trigger a refresh event
        hass.bus.async_fire(f"{DOMAIN}_scan_complete", {
            "duplicates": [d for d in scanner._duplicates if d["entity_id"] not in new_list],
            "config": storage.config
        })

    async def handle_fix(call: ServiceCall):
        entity_id = call.data.get("entity_id")
        new_entity_id = call.data.get("new_entity_id")
        await scanner.async_fix_entity_id(entity_id, new_entity_id)

    async def handle_delete(call: ServiceCall):
        entity_id = call.data.get("entity_id")
        await scanner.async_delete_entity(entity_id)

    async def handle_delete_entities(call: ServiceCall):
        entity_ids = call.data.get("entity_ids", [])
        for eid in entity_ids:
            await scanner.async_delete_entity(eid)
        hass.bus.async_fire(f"{DOMAIN}_delete_complete", {})

    async def handle_rename_entities(call: ServiceCall):
        entity_ids = call.data.get("entity_ids", [])
        all_dups = scanner._duplicates
        for eid in entity_ids:
            item = next((d for d in all_dups if d["entity_id"] == eid), None)
            if item:
                await scanner.async_fix_entity_id(eid, item["base_entity"])
        hass.bus.async_fire(f"{DOMAIN}_scan_complete", {
            "duplicates": scanner._duplicates,
            "config": storage.config
        })

    hass.services.async_register(DOMAIN, SERVICE_SCAN, handle_scan)
    hass.services.async_register(DOMAIN, SERVICE_FIX, handle_fix)
    hass.services.async_register(DOMAIN, SERVICE_DELETE, handle_delete)
    hass.services.async_register(DOMAIN, "delete_entities", handle_delete_entities)
    hass.services.async_register(DOMAIN, "rename_entities_to_base", handle_rename_entities)
    hass.services.async_register(DOMAIN, "save_settings", handle_save_settings)
    hass.services.async_register(DOMAIN, "exclude_entities", handle_exclude_entities)

    return True


async def _setup_static_resources(hass: HomeAssistant) -> None:
    """Register static resources for Lovelace card."""
    try:
        www_path = Path(hass.config.path(f"custom_components/{DOMAIN}/www/{DOMAIN}_card"))

        if not www_path.exists():
            _LOGGER.error("Frontend resources not found at %s", www_path)
            return

        if "http" in hass.config.components:
            if HAS_STATIC_PATH_CONFIG:
                await hass.http.async_register_static_paths(
                    [StaticPathConfig(url_path=f"/{DOMAIN}_card", path=www_path)]
                )
            else:
                hass.http.async_register_static_path(
                    url_path=f"/{DOMAIN}_card", path=str(www_path)
                )
        
        integration = await async_get_integration(hass, DOMAIN)
        version = integration.version

        if "frontend" in hass.config.components:
            add_extra_js_url(hass, f"/{DOMAIN}_card/entity-duplicates-manager-card.js?v={version}")
            add_extra_js_url(hass, f"/{DOMAIN}_card/card-picker-metadata.js?v={version}")
            _LOGGER.info("✅ Lovelace card registered: /%s_card/entity-duplicates-manager-card.js", DOMAIN)

    except Exception as e:
        _LOGGER.error("Failed to setup static resources: %s", e, exc_info=True)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN)
    return unload_ok