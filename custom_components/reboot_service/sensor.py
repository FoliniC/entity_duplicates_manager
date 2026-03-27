import logging
from homeassistant.components.sensor import SensorEntity
from . import DOMAIN
from .reboot_router import _async_fetch_ssid

from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

# Aggiorna ogni 5 minuti come i binary sensors
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    _LOGGER.info(f"{DOMAIN} - Setting up SSID sensor platform")
    async_add_entities([SSIDSensor(hass)], True)


class SSIDSensor(SensorEntity):
    """Representation of the SSID sensor."""

    def __init__(self, hass):
        """Initialize the sensor."""
        self._hass = hass
        self._attr_name = "Router SSID"
        self._attr_unique_id = f"{DOMAIN}_router_ssid"
        self._attr_should_poll = True
        self._attr_native_value = None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._attr_native_value

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            _LOGGER.debug(f"{DOMAIN} - SSID sensor update started")
            # Usa la cache se disponibile (force_refresh=False)
            ssid = await _async_fetch_ssid(self._hass, force_refresh=False)
            
            if ssid is not None:
                self._attr_native_value = ssid
                _LOGGER.info(f"{DOMAIN} - SSID sensor updated to: {ssid}")
            else:
                # Se ssid è None, non resettare necessariamente a unknown se avevamo un valore,
                # ma qui seguiamo la logica della raggiungibilità.
                # Se il router non è raggiungibile, l'SSID è effettivamente ignoto.
                self._attr_native_value = None
                _LOGGER.warning(f"{DOMAIN} - Failed to fetch SSID for sensor (returned None)")
                
        except Exception as e:
            _LOGGER.error(f"{DOMAIN} - Error updating SSID sensor: {str(e)}", exc_info=True)
