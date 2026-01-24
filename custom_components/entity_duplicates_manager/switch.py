"""Switch platform for Entity Duplicates Manager."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Switch Platform."""
    async_add_entities([ConfirmDeletionSwitch(hass)])


class ConfirmDeletionSwitch(RestoreEntity, SwitchEntity):
    """Representation of the Confirm Deletion Switch."""

    _attr_has_entity_name = True
    _attr_name = "Confirm Deletion"
    _attr_unique_id = "duplicate_confirm_deletion"
    _attr_icon = "mdi:alert-circle-check"

    def __init__(self, hass):
        self.hass = hass
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        self._attr_is_on = False
        self.async_write_ha_state()
