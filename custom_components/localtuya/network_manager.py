"""Network manager for cloud-only device monitoring."""

import asyncio
import logging
from typing import Callable, Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from .network_watcher import TuyaNetworkWatcher, NetworkEvent, create_network_watcher
from .network_watchdog import TuyaNetworkWatchdog, async_setup_network_watchdog
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Signal for device network activity
SIGNAL_TUYA_DEVICE_NETWORK_ACTIVITY = "tuya_device_network_activity"


class TuyaNetworkManager:
    """Manages network monitoring for cloud-only devices."""

    def __init__(self, hass: HomeAssistant, coordinator, config_entry):
        """Initialize the network manager.
        
        Args:
            hass: Home Assistant instance
            coordinator: The LocalTuya coordinator instance
            config_entry: The config entry for this integration
        """
        self.hass = hass
        self.coordinator = coordinator
        self._config_entry = config_entry
        self._watcher = None
        self._watchdog = None
        self._device_macs: dict[str, str] = {}  # device_id -> mac
        self._unsub_dispatcher = None

    async def async_start(self) -> None:
        """Start the network manager."""
        # Register cloud-only devices from config
        await self._register_cloud_only_devices()
        
        if self._device_macs:
            # Create watchdog first so it can be passed to the watcher
            self._watchdog = await async_setup_network_watchdog(
                self.hass, self, self._send_notification
            )
            
            try:
                self._watcher = await create_network_watcher(
                    self.hass,
                    self._device_macs,
                    self._handle_network_event,
                    self._watchdog,
                )
            except FileNotFoundError as err:
                self._watcher = None
                _LOGGER.warning(
                    "Network watcher disabled because a required command is missing: %s",
                    err,
                )
            except OSError as err:
                self._watcher = None
                _LOGGER.warning("Network watcher disabled: %s", err)
            else:
                _LOGGER.info(
                    "Network manager started with %d cloud-only devices",
                    len(self._device_macs),
                )
                
                # Start watchdog
                self._watchdog = await async_setup_network_watchdog(
                    self.hass, self, self._send_notification
                )
        else:
            _LOGGER.info("No cloud-only devices to monitor")

    async def _send_notification(self, title: str, message: str) -> None:
        """Send notification via HA persistent notification."""
        try:
            from homeassistant.components.persistent_notification import async_create
            async_create(self.hass, message, title, "tuya_network_watchdog")
        except Exception as e:
            _LOGGER.error("Failed to send watchdog notification: %s", e)

    async def _register_cloud_only_devices(self) -> None:
        """Register cloud-only devices from config entry."""
        config_entry = self._config_entry
        devices = config_entry.data.get("devices", {})
        
        for device_id, dev_config in config_entry.data.get("devices", {}).items():
            # Check if device is cloud-only (sleep time > 0 or placeholder IP)
            is_cloud_only = (
                dev_config.get("device_sleep_time", 0) > 0 
                or dev_config.get("host") == "0.0.0.0"
            )
            
            if is_cloud_only:
                mac = dev_config.get("mac") or dev_config.get("cloud_mac")
                if mac:
                    self._device_macs[device_id] = mac
                    _LOGGER.debug("Registered cloud-only device: %s (MAC: %s)", device_id, mac)
                else:
                    _LOGGER.warning("Cloud-only device %s has no MAC address", device_id)

    @callback
    def _handle_network_event(self, event):
        """Handle network event from watcher."""
        device_id = event.device_id
        event_type = event.event_type
        
        _LOGGER.debug("Network event for %s: %s", event.device_id, event.event_type)
        
        # Fire HA event for coordinator to handle
        self.hass.bus.async_fire(
            "tuya_device_network_activity",
            {
                "device_id": event.device_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "destination_ip": event.destination_ip,
                "destination_port": event.destination_port,
                "protocol": event.protocol,
            }
        )

    async def async_register_device(self, mac: str, device_id: str) -> None:
        """Register a new cloud-only device for monitoring."""
        if device_id in self._device_macs:
            _LOGGER.debug("Device %s already registered", device_id)
            return
        
        self._device_macs[device_id] = mac
        _LOGGER.info("Registered cloud-only device for monitoring: %s (%s)", device_id, mac)
        
        # Restart watcher with updated device list
        if self._watcher:
            await self._watcher.stop()
        
        try:
            self._watcher = await create_network_watcher(
                self.hass,
                self._device_macs,
                self._handle_network_event,
                self._watchdog,
            )
        except OSError as err:
            self._watcher = None
            _LOGGER.warning("Network watcher disabled after registering %s: %s", device_id, err)

    async def async_unregister_device(self, device_id: str) -> None:
        """Unregister a device from monitoring."""
        if device_id not in self._device_macs:
            return
        
        del self._device_macs[device_id]
        _LOGGER.info("Unregistered device from monitoring: %s", device_id)
        
        if self._watcher:
            await self._watcher.stop()
        
        if self._device_macs:
            from .network_watcher import create_network_watcher
            try:
                self._watcher = await create_network_watcher(
                    self.hass,
                    self._device_macs,
                    self._handle_network_event,
                    self._watchdog,
                )
            except OSError as err:
                self._watcher = None
                _LOGGER.warning("Network watcher disabled after unregistering %s: %s", device_id, err)
        else:
            self._watcher = None

    async def async_stop(self) -> None:
        """Stop the network manager."""
        if self._watchdog:
            await self._watchdog.async_stop()
            self._watchdog = None
            
        if self._watcher:
            await self._watcher.stop()
            self._watcher = None
        
        self._device_macs.clear()
        _LOGGER.info("Network manager stopped")

    def get_monitored_devices(self) -> dict[str, str]:
        """Get currently monitored devices."""
        return self._device_macs.copy()

    def get_watchdog_health(self) -> dict:
        """Get watchdog health status for diagnostics."""
        if self._watchdog:
            return self._watchdog.get_health_status()
        return {"watchdog_running": False}


async def async_setup_network_manager(hass, coordinator, config_entry):
    """Set up the network manager for a config entry."""
    manager = TuyaNetworkManager(hass, coordinator, config_entry)
    await manager.async_start()
    return manager
