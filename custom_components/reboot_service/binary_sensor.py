import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from . import DOMAIN
from .reboot_router import _async_fetch_ssid
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import ClientTimeout
from datetime import timedelta

# Binary sensors per monitorare lo stato del repeater e la connettività base.

_LOGGER = logging.getLogger(__name__)

# Aggiorna ogni 5 minuti invece che ogni 30 secondi
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    entities = [
        RouterReachableBinary(hass),
        RouterWifiConnectedBinary(hass)
    ]
    async_add_entities(entities, True)


class RouterReachableBinary(BinarySensorEntity):
    """Raggiungibilità del repeater (login + fetch pagina)."""

    def __init__(self, hass):
        self._hass = hass
        self._attr_name = "Router reachable"
        self._attr_unique_id = f"{DOMAIN}_router_reachable"
        self._is_on = False
        self._attr_device_class = "connectivity"
        self._attr_should_poll = True  # Abilita polling ma con SCAN_INTERVAL lungo

    @property
    def is_on(self):
        return self._is_on

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def should_poll(self):
        """Enable polling with custom interval."""
        return True

    async def async_update(self):
        """Aggiornamento periodico ogni 5 minuti."""
        # Usa la cache - non forza refresh
        ssid = await _async_fetch_ssid(self._hass, force_refresh=False)
        self._is_on = ssid is not None
        _LOGGER.debug(f"{DOMAIN} - Router reachable: {self._is_on}")


class RouterWifiConnectedBinary(BinarySensorEntity):
    """Connessione Wi‑Fi del repeater verso l'upstream (heuristica)."""

    def __init__(self, hass):
        self._hass = hass
        self._attr_name = "Router WiFi connected"
        self._attr_unique_id = f"{DOMAIN}_router_wifi_connected"
        self._is_on = False
        self._attr_device_class = "connectivity"
        self._attr_should_poll = True  # Abilita polling ma con SCAN_INTERVAL lungo

    @property
    def is_on(self):
        return self._is_on

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def should_poll(self):
        """Enable polling with custom interval."""
        return True

    async def async_update(self):
        """Aggiornamento periodico ogni 5 minuti."""
        # Heuristica 1: pagina repeater raggiungibile -> probabilmente è collegato
        # Usa la cache - non forza refresh
        ssid = await _async_fetch_ssid(self._hass, force_refresh=False)
        if not ssid:
            self._is_on = False
            _LOGGER.debug(f"{DOMAIN} - Router WiFi connected: False (no SSID)")
            return

        # Heuristica 2: prova una chiamata veloce a generate_204 (indizio di internet up)
        try:
            session = async_get_clientsession(self._hass)
            timeout = ClientTimeout(total=5)
            async with session.get("http://connectivitycheck.gstatic.com/generate_204", timeout=timeout) as resp:
                self._is_on = resp.status == 204
                _LOGGER.debug(f"{DOMAIN} - Router WiFi connected: {self._is_on}")
        except Exception as e:
            self._is_on = False
            _LOGGER.debug(f"{DOMAIN} - Router WiFi connected: False (connectivity check failed: {e})")