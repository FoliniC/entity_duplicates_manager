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

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["number", "text", "switch", "sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Entity Duplicates Manager from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Register static resources for Lovelace card
    await _setup_static_resources(hass)

    scanner = DuplicatesScanner(hass)
    hass.data[DOMAIN]["scanner"] = scanner

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_scan(call: ServiceCall):
        """Handle the scan service."""
        limit = 5
        exclude = ["sensor.uptime*", "group.*"]

        limit_state = hass.states.get("number.suffix_filter_max")
        if limit_state:
            try:
                limit = int(float(limit_state.state))
            except ValueError:
                pass

        exclude_state = hass.states.get("text.exclude_patterns")
        if exclude_state:
            exclude = [p.strip() for p in exclude_state.state.split(",") if p.strip()]

        _LOGGER.info(f"Scanning with limit={limit} and exclude={exclude}")
        scanner.scan(limit, exclude)

    async def handle_fix(call: ServiceCall):
        entity_id = call.data["entity_id"]
        new_entity_id = call.data["new_entity_id"]
        await scanner.async_fix_entity_id(entity_id, new_entity_id)

    async def handle_delete(call: ServiceCall):
        entity_id = call.data["entity_id"]
        await scanner.async_delete_entity(entity_id)

    hass.services.async_register(DOMAIN, SERVICE_SCAN, handle_scan)
    hass.services.async_register(DOMAIN, SERVICE_FIX, handle_fix)
    hass.services.async_register(DOMAIN, SERVICE_DELETE, handle_delete)

    return True


async def _setup_static_resources(hass: HomeAssistant) -> None:
    """Register static resources for Lovelace card."""
    try:
        # Match Cronostar structure: custom_components/DOMAIN/www/DOMAIN_card
        www_path = Path(hass.config.path(f"custom_components/{DOMAIN}/www/{DOMAIN}_card"))

        if not www_path.exists():
            _LOGGER.error("Frontend resources not found at %s", www_path)
            return

        # Register static path for card files
        if "http" in hass.config.components:
            if HAS_STATIC_PATH_CONFIG:
                await hass.http.async_register_static_paths(
                    [StaticPathConfig(url_path=f"/{DOMAIN}_card", path=www_path)]
                )
            else:
                hass.http.async_register_static_path(
                    url_path=f"/{DOMAIN}_card", path=str(www_path)
                )
        
        # Get integration version for cache busting
        integration = await async_get_integration(hass, DOMAIN)
        version = integration.version

        # Add JS modules to frontend
        if "frontend" in hass.config.components:
            add_extra_js_url(
                hass, 
                f"/{DOMAIN}_card/entity-duplicates-manager-card.js?v={version}"
            )
            add_extra_js_url(
                hass, 
                f"/{DOMAIN}_card/card-picker-metadata.js?v={version}"
            )
            _LOGGER.info("✅ Lovelace card registered: /%s_card/entity-duplicates-manager-card.js", DOMAIN)

    except Exception as e:
        _LOGGER.error("Failed to setup static resources: %s", e, exc_info=True)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN)
    return unload_ok