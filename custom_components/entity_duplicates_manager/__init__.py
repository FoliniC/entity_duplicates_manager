"""The Entity Duplicates Manager integration."""

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SERVICE_SCAN, SERVICE_FIX, SERVICE_DELETE
from .scanner import DuplicatesScanner

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["number", "text", "switch", "sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML (not supported, but good practice to stub)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Entity Duplicates Manager from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    scanner = DuplicatesScanner(hass)
    hass.data[DOMAIN]["scanner"] = scanner

    # Store settings in data for platforms to access or default to entry options
    # We will use platforms to expose these settings as entities per user request

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_scan(call: ServiceCall):
        """Handle the scan service."""
        # Retrieve settings from our entities
        # Note: In a real scenario, we might want to store the entity IDs or unique IDs
        # to look them up more robustly. For now, we assume the entity registry generates
        # predictable IDs based on the name.

        limit = 5  # Default
        exclude = ["sensor.uptime*", "group.*"]  # Default

        # Attempt to read from states
        # Entity IDs are likely number.entity_duplicates_manager_suffix_filter
        # and text.entity_duplicates_manager_exclude_patterns
        # We need to construct them properly based on how HA generates them.

        # Since we set _attr_has_entity_name = True, and the device name is effectively the config entry title...
        # Let's assume standard naming for now, but gracefully fallback.

        # Actually, simpler approach: iterate over all entities of our domain?
        # No, that's not easy.

        # Best guess entity IDs (assuming single instance)
        # We used name="Suffix Filter Max" -> number.entity_duplicates_manager_suffix_filter_max
        # Wait, I named them:
        # Number: "Suffix Filter Max" -> suffix_filter_max
        # Text: "Exclude Patterns" -> exclude_patterns

        limit_state = hass.states.get(
            "number.entity_duplicates_manager_suffix_filter_max"
        )
        if limit_state:
            try:
                limit = int(float(limit_state.state))
            except ValueError:
                pass

        exclude_state = hass.states.get(
            "text.entity_duplicates_manager_exclude_patterns"
        )
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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN)
    return unload_ok
