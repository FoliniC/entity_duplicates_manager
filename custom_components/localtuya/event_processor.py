"""Event processor for cloud-only device network events.

This module handles network events from cloud-only devices, applies configurable
delay and cooldown, and triggers cloud state polling via Tuya Open API.
"""

import asyncio
import logging
import time
from typing import Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_CLOUD_POLLING_ENABLED,
    CONF_CLOUD_POLL_DELAY,
    CONF_CLOUD_POLL_COOLDOWN,
)

_LOGGER = logging.getLogger(__name__)


class TuyaEventProcessor:
    """Processes network events for cloud-only devices and triggers delayed cloud polling."""

    def __init__(self, hass: HomeAssistant, hass_data, entry: ConfigEntry):
        """Initialize the event processor.
        
        Args:
            hass: Home Assistant instance
            hass_data: HassLocalTuyaData storing cloud_data and devices
            entry: ConfigEntry instance
        """
        self.hass = hass
        self.hass_data = hass_data
        self.entry = entry
        self._pending_polls: dict[str, asyncio.Task] = {}
        self._last_poll_time: dict[str, float] = {}
        self._unsub_dispatcher = None

    @callback
    def async_handle_network_event(self, event) -> None:
        """Handle network activity event from network watcher via HA Event Bus."""
        event_data = event.data if hasattr(event, "data") else event
        device_id = event_data.get("device_id")
        event_type = event_data.get("event_type", "unknown")
        
        if not device_id:
            return

        # Check if cloud polling is enabled for this device
        dev_config = self.entry.data.get("devices", {}).get(device_id, {})
        if not dev_config.get("cloud_polling_enabled", True):
            _LOGGER.debug("Cloud polling disabled for %s", device_id)
            return

        # Check if a poll is already scheduled for this device
        if device_id in self._pending_polls:
            _LOGGER.debug("Poll already pending for %s — skipping duplicate trigger", device_id)
            return

        # Check cooldown since last completed poll
        cooldown = self._get_cooldown(device_id)
        last_poll = self._last_poll_time.get(device_id, 0)
        if time.time() - last_poll < cooldown:
            _LOGGER.debug("Skipping cloud poll for %s (cooldown active)", device_id)
            return

        # Get delay (give device a few seconds to finish uploading to cloud)
        delay = self._get_delay(device_id)
        _LOGGER.info("Network activity detected for %s (%s) — scheduling cloud poll in %ss", device_id, event_type, delay)
        
        # Schedule delayed cloud poll
        task = asyncio.create_task(self._delayed_poll_wrapper(device_id, delay))
        self._pending_polls[device_id] = task

    def _get_delay(self, device_id: str) -> int:
        """Get polling delay for device."""
        device_config = self.entry.data.get("devices", {}).get(device_id, {})
        return device_config.get("cloud_poll_delay", 3)

    def _get_cooldown(self, device_id: str) -> int:
        """Get cooldown period for device."""
        device_config = self.entry.data.get("devices", {}).get(device_id, {})
        return device_config.get("cloud_poll_cooldown", 15)

    async def _delayed_poll_wrapper(self, device_id: str, delay: float) -> None:
        """Wrapper to handle delayed polling with cleanup."""
        try:
            _LOGGER.info("Waiting %ss before querying Tuya Cloud for %s...", delay, device_id)
            await asyncio.sleep(delay)
            await self._poll_and_update(device_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            _LOGGER.error("Error in delayed cloud poll for %s: %s", device_id, e)
        finally:
            self._pending_polls.pop(device_id, None)

    async def _poll_and_update(self, device_id: str) -> None:
        """Poll cloud state and update local device state."""
        try:
            _LOGGER.info("Querying Tuya Cloud API for device %s state...", device_id)
            cloud_api = self.hass_data.cloud_data
            
            # Query device properties from cloud shadow
            result, status = await cloud_api.async_get_device_query_properties(device_id)
            if status != "ok":
                _LOGGER.warning("Failed to query cloud state for %s: %s", device_id, status)
                return

            properties = result.get("properties", [])
            dps_state = {}
            for prop in properties:
                dp_id = str(prop.get("dp_id", ""))
                value = prop.get("value")
                if dp_id and value is not None:
                    dps_state[dp_id] = value
                    # Map 3-digit cloud DP IDs (e.g. 101, 102) to 1-digit/2-digit local DP IDs (1, 2)
                    if dp_id.isdigit() and int(dp_id) >= 100:
                        short_id = str(int(dp_id) % 100)
                        if short_id not in dps_state:
                            dps_state[short_id] = value

            _LOGGER.info("Cloud poll result for %s (with mapped DPS): %s", device_id, dps_state)
            
            # Update local TuyaDevice status if present
            from homeassistant.helpers.dispatcher import async_dispatcher_send
            device = self.hass_data.devices.get(device_id)
            if device and dps_state:
                device.status_updated(dps_state)
                _LOGGER.info("Successfully updated device %s status from cloud!", device_id)
            
            # Always dispatch to entities registered for this device_id
            async_dispatcher_send(self.hass, f"localtuya_{device_id}", dps_state)
            _LOGGER.info("Dispatched cloud status update for %s directly to entities: %s", device_id, dps_state)

            self._last_poll_time[device_id] = time.time()
        except Exception as e:
            _LOGGER.error("Failed to poll cloud state for %s: %s", device_id, e)


async def async_setup_event_processor(hass: HomeAssistant, hass_data, entry: ConfigEntry):
    """Set up the event processor for a config entry."""
    processor = TuyaEventProcessor(hass, hass_data, entry)
    
    # Register HA Event Bus listener (network_manager fires event via hass.bus.async_fire)
    unsub = hass.bus.async_listen(
        "tuya_device_network_activity", processor.async_handle_network_event
    )
    processor._unsub_dispatcher = unsub
    
    return processor