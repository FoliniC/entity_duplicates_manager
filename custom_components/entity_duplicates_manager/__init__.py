"""The Entity Duplicates Manager integration."""

import logging
from pathlib import Path

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration
from homeassistant.components.frontend import add_extra_js_url

try:
    from homeassistant.components.http import StaticPathConfig
    HAS_STATIC_PATH_CONFIG = True
except ImportError:
    HAS_STATIC_PATH_CONFIG = False

from .const import (
    DOMAIN,
    SERVICE_SCAN,
    SERVICE_FIX,
    SERVICE_DELETE,
    SERVICE_RENAME,
    SERVICE_DELETE_ENTITIES,
    SERVICE_GET_ENTITIES,
    EVENT_SCAN_COMPLETE,
    EVENT_DELETE_COMPLETE,
    EVENT_ENTITIES,
    DEFAULT_SUFFIX_MAX,
)
from .scanner import DuplicatesScanner
from .storage import StorageManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["number", "text", "switch", "sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SCAN_SCHEMA = vol.Schema(
    {
        vol.Optional("max_suffix", default=DEFAULT_SUFFIX_MAX): vol.All(
            cv.positive_int, vol.Range(min=1, max=99)
        ),
        vol.Optional("exclusion_patterns", default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
    }
)

DELETE_ENTITIES_SCHEMA = vol.Schema(
    {
        vol.Required("entity_ids"): vol.All(
            cv.ensure_list, [cv.entity_id], vol.Length(max=500)
        ),
        vol.Optional("dry_run", default=False): cv.boolean,
        vol.Optional("force", default=False): cv.boolean,
    }
)

GET_ENTITIES_SCHEMA = vol.Schema(
    {
        vol.Optional("domain"): cv.string,
        vol.Optional("search"): cv.string,
    }
)

async def _require_admin(hass: HomeAssistant, call: ServiceCall) -> None:
    """Accept only calls from an admin user (e.g., from UI)."""
    user_id = call.context.user_id
    user = await hass.auth.async_get_user(user_id) if user_id else None
    if user is None or not user.is_admin:
        raise Unauthorized(context=call.context)

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
        
        scanner.fire_scan_complete(filtered_results, storage.config)

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
        scanner.fire_scan_complete(
            [d for d in scanner._duplicates if d["entity_id"] not in new_list],
            storage.config,
        )

    async def handle_fix(call: ServiceCall):
        entity_id = call.data.get("entity_id")
        new_entity_id = call.data.get("new_entity_id")
        await scanner.async_fix_entity_id(entity_id, new_entity_id)

    async def handle_delete(call: ServiceCall):
        entity_id = call.data.get("entity_id")
        await scanner.async_delete_entity(entity_id)

    async def handle_delete_entities(call: ServiceCall):
        """Secure delete with admin check, dry_run, force, and re-validation."""
        await _require_admin(hass, call)

        dry_run = call.data["dry_run"]
        results = await scanner.delete_entities(
            call.data["entity_ids"],
            dry_run=dry_run,
            force=call.data["force"],
        )
        hass.bus.async_fire(EVENT_DELETE_COMPLETE, {**results, "dry_run": dry_run})
        return results

    async def handle_get_entities(call: ServiceCall):
        """Get all entities for the entity manager tab."""
        results = scanner.get_all_entities(
            domain_filter=call.data.get("domain"),
            search=call.data.get("search"),
        )
        hass.bus.async_fire(EVENT_ENTITIES, {"entities": results})
        return {"entities": results}

    async def handle_rename_entities(call: ServiceCall):
        entity_ids = call.data.get("entity_ids", [])
        all_dups = scanner._duplicates
        renamed_count = 0
        skipped_count = 0
        for eid in entity_ids:
            item = next((d for d in all_dups if d["entity_id"] == eid), None)
            if item:
                if not item.get("can_rename", True):
                    skipped_count += 1
                    _LOGGER.warning(
                        "Skipping rename for %s because it is not in the entity registry",
                        eid,
                    )
                    continue

                if await scanner.async_fix_entity_id(eid, item["base_entity"]):
                    renamed_count += 1
                else:
                    skipped_count += 1
        _LOGGER.info(
            "Rename to base complete: renamed=%s skipped=%s requested=%s",
            renamed_count,
            skipped_count,
            len(entity_ids),
        )
        scanner.fire_scan_complete(scanner._duplicates, storage.config)

    hass.services.async_register(
        DOMAIN, SERVICE_SCAN, handle_scan,
        schema=SCAN_SCHEMA, supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FIX, handle_fix,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE, handle_delete,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DELETE_ENTITIES, handle_delete_entities,
        schema=DELETE_ENTITIES_SCHEMA, supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_GET_ENTITIES, handle_get_entities,
        schema=GET_ENTITIES_SCHEMA, supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RENAME, handle_rename_entities,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, "save_settings", handle_save_settings,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, "exclude_entities", handle_exclude_entities,
        supports_response=SupportsResponse.OPTIONAL,
    )

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
