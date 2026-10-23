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
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Number of attempts (and delay between them) when querying the Tuya cloud for
# a sleepy device's state. These sensors report once per wake-up, so a single
# transient network error would lose the reading until the next wake-up.
CLOUD_POLL_RETRIES = 3
CLOUD_POLL_RETRY_DELAY = 3


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

    @property
    def _current_hass_data(self):
        """Return the live hass data for this entry.

        The entry is reloaded on every config change, which replaces the
        cloud API instance. Always resolve it from hass.data so a stale
        processor never polls with an outdated (and possibly token-less)
        cloud API instance.
        """
        return self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id) or self.hass_data

    async def async_stop(self) -> None:
        """Stop the event processor and release its event bus listener."""
        if self._unsub_dispatcher:
            self._unsub_dispatcher()
            self._unsub_dispatcher = None
        for task in self._pending_polls.values():
            task.cancel()
        self._pending_polls.clear()
        _LOGGER.debug("Event processor stopped")

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
            hass_data = self._current_hass_data
            cloud_api = hass_data.cloud_data

            # Query device properties from cloud shadow. Retry a couple of
            # times: these sensors report once per wake-up, so a single
            # transient network error would otherwise lose the reading until
            # the next wake-up (up to an hour later).
            result, status = {}, "not attempted"
            for attempt in range(1, CLOUD_POLL_RETRIES + 1):
                _LOGGER.info(
                    "Querying Tuya Cloud API for device %s state... (attempt %s/%s)",
                    device_id,
                    attempt,
                    CLOUD_POLL_RETRIES,
                )
                result, status = await cloud_api.async_get_device_query_properties(
                    device_id
                )
                if status == "ok":
                    break
                if attempt < CLOUD_POLL_RETRIES:
                    _LOGGER.warning(
                        "Failed to query cloud state for %s: %s — retrying in %ss",
                        device_id,
                        status,
                        CLOUD_POLL_RETRY_DELAY,
                    )
                    await asyncio.sleep(CLOUD_POLL_RETRY_DELAY)

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
            device = hass_data.devices.get(device_id)
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