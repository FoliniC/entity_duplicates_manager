#!/usr/bin/env python3
"""
Capture script for LocalTuya device messages - Running inside Home Assistant.
This version uses the Home Assistant Python API directly (runs as a script in HA).
Captures all messages for the balcony device (bfbf8ab6b500e77408pupf) 
to understand why it turns on unexpectedly.

Usage inside HA:
    python3 /config/helpers/capture_balcone_device_internal.py

Or as a service call:
    hass.services.call('python_script', 'capture_balcone', {})
"""

import json
import logging
from datetime import datetime
from pathlib import Path

_LOGGER = logging.getLogger("balcone_capture")

# Configuration
DEVICE_ID = "bfbf8ab6b500e77408pupf"
ENTITY_ID = "switch.luce_balcone_switch_1"
OUTPUT_FILE = Path("/config/logs/balcone_capture.jsonl")

# Global capture state
_capture_active = False
_listeners = []


def write_event(event_type: str, data: dict):
    """Write event to JSONL file."""
    record = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "data": data
    }
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def handle_localtuya_status_update(event):
    """Handle localtuya_status_update event."""
    event_data = event.data
    device_id = event_data.get("device_id")
    
    if device_id == DEVICE_ID:
        write_event("localtuya_status_update", event_data)
        _LOGGER.warning(f"[LOCALTUYA_STATUS] Device: {device_id}, Data: {event_data}")


def handle_localtuya_device_dp_triggered(event):
    """Handle localtuya_device_dp_triggered event."""
    event_data = event.data
    device_id = event_data.get("device_id")
    
    if device_id == DEVICE_ID:
        write_event("localtuya_device_dp_triggered", event_data)
        _LOGGER.warning(f"[LOCALTUYA_DP_TRIGGERED] Device: {device_id}, Data: {event_data}")


def handle_state_changed(event):
    """Handle state_changed event for balcony switch."""
    event_data = event.data
    entity_id = event_data.get("entity_id")
    
    if entity_id == ENTITY_ID:
        new_state = event_data.get("new_state")
        old_state = event_data.get("old_state")
        
        write_event("state_changed", {
            "entity_id": entity_id,
            "old_state": str(old_state.state) if old_state else None,
            "new_state": str(new_state.state) if new_state else None,
            "old_attributes": dict(old_state.attributes) if old_state else {},
            "new_attributes": dict(new_state.attributes) if new_state else {},
            "context": {
                "user_id": str(new_state.context.user_id) if new_state and new_state.context else None,
                "parent_id": str(new_state.context.parent_id) if new_state and new_state.context else None,
                "id": str(new_state.context.id) if new_state and new_state.context else None,
            } if new_state else None
        })
        _LOGGER.warning(f"[STATE_CHANGED] Entity: {entity_id}, Old: {old_state.state if old_state else None}, New: {new_state.state if new_state else None}, Context: {new_state.context if new_state else None}")


def handle_automation_triggered(event):
    """Handle automation_triggered event for anti-accensione."""
    event_data = event.data
    entity_id = event_data.get("entity_id")
    
    if entity_id == "automation.anti_accensione_balcone":
        write_event("automation_triggered", event_data)
        _LOGGER.warning(f"[AUTOMATION_TRIGGERED] {event_data}")


def start_capture(hass):
    """Start capturing events."""
    global _capture_active, _listeners
    
    if _capture_active:
        _LOGGER.warning("Capture already active")
        return
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear or backup output file
    if OUTPUT_FILE.exists():
        backup = OUTPUT_FILE.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
        OUTPUT_FILE.rename(backup)
        _LOGGER.info(f"Previous capture backed up to {backup}")
    
    # Subscribe to events
    _listeners = [
        hass.bus.async_listen("localtuya_status_update", handle_localtuya_status_update),
        hass.bus.async_listen("localtuya_device_dp_triggered", handle_localtuya_device_dp_triggered),
        hass.bus.async_listen("state_changed", handle_state_changed),
        hass.bus.async_listen("automation_triggered", handle_automation_triggered),
    ]
    
    _capture_active = True
    _LOGGER.warning(f"✅ CAPTURE STARTED for device {DEVICE_ID} (entity: {ENTITY_ID})")
    _LOGGER.warning(f"📝 Output file: {OUTPUT_FILE}")
    _LOGGER.warning("📋 Listening for: localtuya_status_update, localtuya_device_dp_triggered, state_changed, automation_triggered")


def stop_capture(hass):
    """Stop capturing events."""
    global _capture_active, _listeners
    
    if not _capture_active:
        _LOGGER.warning("Capture not active")
        return
    
    for unsub in _listeners:
        unsub()
    _listeners = []
    _capture_active = False
    
    _LOGGER.warning("🛑 CAPTURE STOPPED")


def status_capture():
    """Return capture status."""
    return {
        "active": _capture_active,
        "device_id": DEVICE_ID,
        "entity_id": ENTITY_ID,
        "output_file": str(OUTPUT_FILE),
        "listeners_count": len(_listeners)
    }


# Allow running as a script (when executed in HA's python environment)
if __name__ == "__main__":
    # This won't work standalone - needs HA context
    print("This script must run inside Home Assistant context.")
    print("Use: python3 -m helpers.capture_balcone_device_internal")
    print("Or call via HA service: python_script.capture_balcone")