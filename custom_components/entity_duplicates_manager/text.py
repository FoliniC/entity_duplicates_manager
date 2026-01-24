"""Text platform for Entity Duplicates Manager."""

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_EXCLUDE_PATTERN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Text Platform."""
    async_add_entities([DuplicateExcludePattern(hass)])


class DuplicateExcludePattern(RestoreEntity, TextEntity):
    """Representation of the Exclude Pattern Text."""

    _attr_has_entity_name = True
    _attr_name = "Exclude Patterns"
    _attr_unique_id = "duplicate_exclude_pattern"
    _attr_icon = "mdi:filter-variant"

    def __init__(self, hass):
        self.hass = hass
        self._attr_native_value = DEFAULT_EXCLUDE_PATTERN

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_native_value = last_state.state

    async def async_set_value(self, value: str) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()
