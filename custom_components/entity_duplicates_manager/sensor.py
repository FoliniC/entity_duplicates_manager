"""Sensor platform for Entity Duplicates Manager."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import EVENT_SCAN_COMPLETE


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Sensor Platform."""
    async_add_entities([DuplicatesCountSensor(hass)])


class DuplicatesCountSensor(RestoreEntity, SensorEntity):
    """Representation of the Duplicates Count Sensor."""

    _attr_has_entity_name = True
    _attr_name = "Duplicates Found"
    _attr_unique_id = "duplicate_count_sensor"
    _attr_native_unit_of_measurement = "entities"
    _attr_icon = "mdi:counter"

    def __init__(self, hass):
        self.hass = hass
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = int(last_state.state)
            except ValueError:
                pass

        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_SCAN_COMPLETE, self._handle_scan_complete)
        )

    @callback
    def _handle_scan_complete(self, event):
        """Update state when scan is complete."""
        self._attr_native_value = event.data.get("count", 0)
        self._attr_extra_state_attributes = {
            "duplicates": event.data.get("duplicates", [])
        }
        self.async_write_ha_state()
