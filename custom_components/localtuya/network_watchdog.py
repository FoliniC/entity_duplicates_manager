"""Network watchdog for Tuya cloud-only device monitoring.

This module provides a watchdog that monitors the network watcher health
and sends notifications via HA when issues are detected.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable, Awaitable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Watchdog check interval (seconds)
WATCHDOG_CHECK_INTERVAL = 60
# Max seconds without any packet before considering watcher stalled (set to 4 hours, since sleepy sensors stay idle)
MAX_STALL_SECONDS = 14400
# Max SSH failures before alert
MAX_SSH_FAILURES = 3


@dataclass
class WatcherHealth:
    """Health status of the network watcher."""
    is_running: bool = False
    last_packet_time: Optional[float] = None
    last_ssh_check_time: Optional[float] = None
    ssh_failure_count: int = 0
    tcpdump_restart_count: int = 0
    last_notification_time: Optional[float] = None
    notification_cooldown: int = 3600  # 1 hour between same-type notifications


class TuyaNetworkWatchdog:
    """Watchdog for the network watcher."""

    def __init__(
        self,
        hass: HomeAssistant,
        network_manager,  # TuyaNetworkManager instance
        notify_callback: Optional[Callable[[str, str], Awaitable[None]]] = None,
    ):
        """Initialize the watchdog.

        Args:
            hass: Home Assistant instance
            network_manager: The TuyaNetworkManager instance to monitor
            notify_callback: Async callback(title, message) for sending notifications
        """
        self.hass = hass
        self._network_manager = network_manager
        self._notify = notify_callback or self._default_notify
        self._health = WatcherHealth()
        self._unsub_watchdog: Optional[Callable] = None
        self._running = False

    async def _default_notify(self, title: str, message: str) -> None:
        """Default notification via HA persistent notification."""
        try:
            self.hass.bus.async_fire(
                "notify",
                {
                    "title": title,
                    "message": message,
                },
            )
            # Also create persistent notification
            from homeassistant.components.persistent_notification import async_create
            async_create(self.hass, message, title, "tuya_network_watchdog")
        except Exception as e:
            _LOGGER.error("Failed to send notification: %s", e)

    def _notify_if_cooldown(self, notification_type: str, title: str, message: str) -> bool:
        """Send notification if cooldown has passed for this type."""
        now = time.time()
        if self._health.last_notification_time is None or \
           now - self._health.last_notification_time > self._health.notification_cooldown:
            self._health.last_notification_time = now
            self.hass.async_create_task(self._notify(title, message))
            return True
        return False

    def record_packet(self) -> None:
        """Record that a packet was received."""
        self._health.last_packet_time = time.time()

    def record_ssh_check(self, success: bool) -> None:
        """Record SSH connectivity check result."""
        self._health.last_ssh_check_time = time.time()
        if success:
            self._health.ssh_failure_count = 0
        else:
            self._health.ssh_failure_count += 1

    def record_tcpdump_restart(self) -> None:
        """Record tcpdump process restart."""
        self._health.tcpdump_restart_count += 1

    async def _check_health(self, now: datetime) -> None:
        """Periodic health check."""
        if not self._running:
            return

        watcher = self._network_manager._watcher
        current_time = time.time()

        # Check 1: Watcher process exists and is running
        if watcher is None:
            if self._health.is_running:
                _LOGGER.warning("Network watcher became None (was running)")
                self._health.is_running = False
                await self._notify_if_cooldown(
                    "watcher_stopped",
                    "⚠️ Tuya Network Watcher Stopped",
                    "The network watcher for cloud-only Tuya devices has stopped. "
                    "Cloud polling will not trigger automatically. Check router SSH connectivity."
                )
            return

        if not watcher._running:
            if self._health.is_running:
                _LOGGER.warning("Network watcher reported not running")
                self._health.is_running = False
                await self._notify_if_cooldown(
                    "watcher_not_running",
                    "⚠️ Tuya Network Watcher Not Running",
                    "The network watcher reports it's not running. "
                    "This may be due to SSH failures or tcpdump issues."
                )
            return

        # Mark as running if we got here
        if not self._health.is_running:
            _LOGGER.info("Network watcher is healthy")
            self._health.is_running = True

        # Check 2: Packet stall detection
        if self._health.last_packet_time:
            stall_seconds = current_time - self._health.last_packet_time
            if stall_seconds > MAX_STALL_SECONDS:
                _LOGGER.warning(
                    "Network watcher stall detected: no packets for %.0f seconds",
                    stall_seconds
                )
                self._notify_if_cooldown(
                    "stall",
                    "⚠️ Tuya Network Watcher Stall",
                    f"No network packets detected for {stall_seconds:.0f} seconds. "
                    f"Cloud-only devices (contact sensors, TH sensors) may not trigger cloud polling. "
                    f"Check router connectivity and device wake-ups."
                )
        else:
            # No packets ever received - check if watcher just started
            if watcher._running and current_time - (self._health.last_ssh_check_time or 0) > 120:
                self._notify_if_cooldown(
                    "no_packets",
                    "⚠️ Tuya Network Watcher: No Packets",
                    "Network watcher is running but no packets have been captured yet. "
                    "This may be normal if devices haven't woken up, or indicate a capture issue."
                )

        # Check 3: SSH failure threshold
        if self._health.ssh_failure_count >= MAX_SSH_FAILURES:
            _LOGGER.error(
                "Network watcher SSH failures: %d (threshold: %d)",
                self._health.ssh_failure_count, MAX_SSH_FAILURES
            )
            self._notify_if_cooldown(
                "ssh_failures",
                "🔴 Tuya Network Watcher: SSH Failures",
                f"SSH to router (192.168.0.11) has failed {self._health.ssh_failure_count} times. "
                f"Network watcher cannot monitor device traffic. "
                f"Check router reachability and SSH key."
            )

        # Check 4: Excessive tcpdump restarts
        if self._health.tcpdump_restart_count > 5:
            self._notify_if_cooldown(
                "restarts",
                "⚠️ Tuya Network Watcher: Frequent Restarts",
                f"tcpdump has been restarted {self._health.tcpdump_restart_count} times. "
                f"This may indicate unstable SSH connection or router issues."
            )

    async def async_start(self) -> None:
        """Start the watchdog."""
        if self._running:
            _LOGGER.warning("Watchdog already running")
            return

        self._running = True
        self._health.is_running = True

        # Schedule periodic health checks
        self._unsub_watchdog = async_track_time_interval(
            self.hass,
            self._check_health,
            timedelta(seconds=WATCHDOG_CHECK_INTERVAL),
        )

        _LOGGER.info("Network watchdog started (check interval: %ss)", WATCHDOG_CHECK_INTERVAL)

    async def async_stop(self) -> None:
        """Stop the watchdog."""
        if self._unsub_watchdog:
            self._unsub_watchdog()
            self._unsub_watchdog = None
        self._running = False
        _LOGGER.info("Network watchdog stopped")

    def get_health_status(self) -> dict:
        """Get current health status for diagnostics."""
        watcher = self._network_manager._watcher
        return {
            "watchdog_running": self._running,
            "watcher_running": watcher._running if watcher else False,
            "watcher_exists": watcher is not None,
            "last_packet_ago": (
                time.time() - self._health.last_packet_time
                if self._health.last_packet_time else None
            ),
            "ssh_failure_count": self._health.ssh_failure_count,
            "tcpdump_restart_count": self._health.tcpdump_restart_count,
            "monitored_devices": len(self._network_manager._device_macs),
        }


async def async_setup_network_watchdog(hass: HomeAssistant, network_manager, notify_callback=None):
    """Set up the network watchdog for a config entry."""
    watchdog = TuyaNetworkWatchdog(hass, network_manager, notify_callback)
    await watchdog.async_start()
    return watchdog