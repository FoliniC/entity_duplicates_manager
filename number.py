"""Number platform for Entity Duplicates Manager."""

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DEFAULT_SUFFIX_MAX


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Number Platform."""
    async_add_entities([DuplicateSuffixFilter(hass)])


class DuplicateSuffixFilter(RestoreEntity, NumberEntity):
    """Representation of the Suffix Max Filter."""

    _attr_has_entity_name = True
    _attr_name = "Suffix Filter Max"
    _attr_unique_id = "duplicate_suffix_filter"
    _attr_native_min_value = 1
    _attr_native_max_value = 10
    _attr_native_step = 1
    _attr_icon = "mdi:numeric"

    def __init__(self, hass):
        self.hass = hass
        self._attr_native_value = DEFAULT_SUFFIX_MAX

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = float(last_state.state)
            except ValueError:
                pass

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()
