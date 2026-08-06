"""Event processor for cloud-only device network events.

This module handles network events from cloud-only devices, applies configurable
delay and cooldown, and triggers cloud state polling.
"""

import asyncio
import logging
import time
from typing import Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    CONF_CLOUD_POLLING_ENABLED,
    CONF_CLOUD_POLL_DELAY,
    CONF_CLOUD_POLL_COOLDOWN,
    CONF_DEVICE_SLEEP_TIME,
    CONF_MAC,
    CONF_MAC_RETRIEVAL,
)

_LOGGER = logging.getLogger(__name__)


class TuyaEventProcessor:
    """Processes network events for cloud-only devices and triggers delayed cloud polling."""

    def __init__(self, hass: HomeAssistant, coordinator):
        """Initialize the event processor.
        
        Args:
            hass: Home Assistant instance
            coordinator: LocalTuya coordinator instance
        """
        self.hass = hass
        self.coordinator = coordinator
        self._pending_polls: dict[str, asyncio.Task] = {}
        self._last_poll_time: dict[str, float] = {}
        self._unsub_dispatcher = None

    @callback
    def async_handle_network_event(self, event_data: dict) -> None:
        """Handle network activity event from network watcher."""
        device_id = event_data.get("device_id")
        event_type = event_data.get("event_type", "unknown")
        
        if not device_id:
            return

        # Check if cloud polling is enabled for this device
        device_config = self.coordinator.config_entry.data.get("devices", {}).get(device_id, {})
        if not device_config.get("cloud_polling_enabled", True):
            _LOGGER.debug("Cloud polling disabled for %s", device_id)
            return

        _LOGGER.debug("Network event for %s: %s", device_id, event_type)
        
        # Check cooldown
        cooldown = self._get_cooldown(device_id)
        last_poll = self._last_poll_time.get(device_id, 0)
        if time.time() - last_poll < cooldown:
            _LOGGER.debug("Skipping cloud poll for %s (cooldown)", device_id)
            return

        # Get delay
        delay = self._get_delay(device_id)
        
        # Cancel any existing pending poll for this device
        if device_id in self._pending_polls:
            self._pending_polls[device_id].cancel()
        
        # Schedule delayed cloud poll
        task = asyncio.create_task(self._delayed_poll_wrapper(device_id, delay))
        self._pending_polls[device_id] = task

    def _get_delay(self, device_id: str) -> int:
        """Get polling delay for device."""
        device_config = self.coordinator.config_entry.data.get("devices", {}).get(device_id, {})
        return device_config.get("cloud_poll_delay", 5)

    def _get_cooldown(self, device_id: str) -> int:
        """Get cooldown period for device."""
        device_config = self.coordinator.config_entry.data.get("devices", {}).get(device_id, {})
        return device_config.get("cloud_poll_cooldown", 30)

    async def _delayed_poll_wrapper(self, device_id: str, delay: float) -> None:
        """Wrapper to handle delayed polling with cleanup."""
        try:
            await asyncio.sleep(delay)
            await self._poll_and_update(device_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            _LOGGER.error("Error in delayed cloud poll for %s: %s", device_id, e)
        finally:
            self._pending_polls.pop(device_id, None)

    async def _poll_and_update(self, device_id: str) -> None:
        """Poll cloud state and update local device."""
        try:
            _LOGGER.info("Polling cloud state for device %s", device_id)
            cloud_state = await self.coordinator.async_poll_cloud_state(device_id)
            
            # Update local state
            device = self.coordinator.devices.get(device_id)
            if device:
                device.status_updated(cloud_state)
                _LOGGER.info("Updated %s from cloud: %s", device_id, cloud_state)
            
            self._last_poll_time[device_id] = asyncio.get_event_loop().time()
        except Exception as e:
            _LOGGER.error("Failed to poll cloud state for %s: %s", device_id, e)

    @callback
    def async_handle_network_event(self, event_data: dict) -> None:
        """Handle network activity event from network watcher."""
        device_id = event_data.get("device_id")
        event_type = event_data.get("event_type", "unknown")
        
        if not device_id:
            return

        # Check if cloud polling is enabled for this device
        device_config = self.coordinator.config_entry.data.get("devices", {}).get(device_id, {})
        if not device_config.get("cloud_polling_enabled", True):
            _LOGGER.debug("Cloud polling disabled for %s", device_id)
            return

        _LOGGER.debug("Network event for %s: %s", device_id, event_type)
        
        # Check cooldown
        cooldown = self._get_cooldown(device_id)
        last_poll = self._last_poll_time.get(device_id, 0)
        if time.time() - last_poll < cooldown:
            _LOGGER.debug("Skipping cloud poll for %s (cooldown)", device_id)
            return

        # Get delay
        delay = self._get_delay(device_id)
        
        # Cancel any existing pending poll for this device
        if device_id in self._pending_polls:
            self._pending_polls[device_id].cancel()
        
        # Schedule delayed cloud poll
        task = asyncio.create_task(self._delayed_poll_wrapper(device_id, delay))
        self._pending_polls[device_id] = task


async def async_setup_event_processor(hass, coordinator):
    """Set up the event processor for a config entry."""
    processor = TuyaEventProcessor(hass, coordinator)
    
    # Register event listener
    from homeassistant.helpers.dispatcher import async_dispatcher_connect
    unsub = async_dispatcher_connect(
        hass, "tuya_device_network_activity", processor.async_handle_network_event
    )
    
    return processor