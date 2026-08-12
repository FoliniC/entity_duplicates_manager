"""HA Clipboards Sensor Entity."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.storage import Store
import voluptuous as vol

from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)

# Service schemas
CREATE_ATTRIBUTE_SCHEMA = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Length(min=1)),
})

SET_ACTIVE_SCHEMA = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Length(min=1)),
})

SAVE_TEXT_SCHEMA = vol.Schema({
    vol.Optional("text", default=""): str,
})

DELETE_ATTRIBUTE_SCHEMA = vol.Schema({
    vol.Required("name"): vol.All(str, vol.Length(min=1)),
})


class HAClipboardsSensor(SensorEntity):
    """Sensor representing the HA Clipboards."""

    _attr_name = "HA Clipboards"
    _attr_unique_id = "ha_clipboards"
    _attr_icon = "mdi:clipboard-text-multiple"

    def __init__(self, hass: HomeAssistant, store: Store, data: Dict[str, Any]) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._store = store
        self._data = data
        self._attr_native_value = self._get_state()

    def _get_state(self) -> str:
        """Get the current state."""
        active = self._data.get("active_attribute")
        if active is None:
            return "no_active"
        return f"active: {active}"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return {
            "attributes": self._data.get("attributes", {}),
            "active_attribute": self._data.get("active_attribute"),
            "attribute_names": list(self._data.get("attributes", {}).keys()),
        }

    async def _save_and_update(self) -> None:
        """Save data to storage and update state."""
        await self._store.async_save(self._data)
        self._attr_native_value = self._get_state()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        pass


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HA Clipboards sensor platform from config entry."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load() or {"attributes": {}, "active_attribute": None}
    
    entity = HAClipboardsSensor(hass, store, data)
    async_add_entities([entity], True)
