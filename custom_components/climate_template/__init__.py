"""The climate template component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "climate_template"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the climate_template component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up climate_template from a config entry."""
    # This component uses platform (YAML) setup, not config entries
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return True