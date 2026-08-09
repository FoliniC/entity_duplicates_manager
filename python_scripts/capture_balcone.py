#!/usr/bin/env python3
"""
Home Assistant Python Script: Capture Balcone Device Messages
This script runs inside Home Assistant and captures all LocalTuya messages
for the balcony device (bfbf8ab6b500e77408pupf).

Usage:
    - Call service: python_script.capture_balcone_start
    - Call service: python_script.capture_balcone_stop
    - Call service: python_script.capture_balcone_status
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

# Global capture state (stored in hass.data)
CAPTURE_KEY = "balcone_capture"


def write_event(hass, event_type: str, data: dict):
    """Write event to JSONL file."""
    record = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "data": data
    }
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


# --- Service handler ---
service = data.get("service", "capture_balcone_status")

hass.data.setdefault(CAPTURE_KEY, {})
capture_data = hass.data[CAPTURE_KEY]

if service == "capture_balcone_start":
    if capture_data.get("active", False):
        _LOGGER.warning("Capture already active")
        output = {"status": "already_active", "message": "Capture already running"}
    else:
        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Backup existing file
        if OUTPUT_FILE.exists():
            backup = OUTPUT_FILE.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
            OUTPUT_FILE.rename(backup)
            _LOGGER.info(f"Previous capture backed up to {backup}")
        
        # Event handlers
        def handle_localtuya_status_update(event):
            event_data = event.data
            device_id = event_data.get("device_id")
            if device_id == DEVICE_ID:
                write_event(hass, "localtuya_status_update", event_data)
                _LOGGER.warning(f"[LOCALTUYA_STATUS] Device: {device_id}, Data: {event_data}")

        def handle_localtuya_device_dp_triggered(event):
            event_data = event.data
            device_id = event_data.get("device_id")
            if device_id == DEVICE_ID:
                write_event(hass, "localtuya_device_dp_triggered", event_data)
                _LOGGER.warning(f"[LOCALTUYA_DP_TRIGGERED] Device: {device_id}, Data: {event_data}")

        def handle_state_changed(event):
            event_data = event.data
            entity_id = event_data.get("entity_id")
            if entity_id == ENTITY_ID:
                new_state = event_data.get("new_state")
                old_state = event_data.get("old_state")
                write_event(hass, "state_changed", {
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
            event_data = event.data
            entity_id = event_data.get("entity_id")
            if entity_id == "automation.anti_accensione_balcone":
                write_event(hass, "automation_triggered", event_data)
                _LOGGER.warning(f"[AUTOMATION_TRIGGERED] {event_data}")

        # Subscribe to events
        capture_data["listeners"] = [
            hass.bus.async_listen("localtuya_status_update", handle_localtuya_status_update),
            hass.bus.async_listen("localtuya_device_dp_triggered", handle_localtuya_device_dp_triggered),
            hass.bus.async_listen("state_changed", handle_state_changed),
            hass.bus.async_listen("automation_triggered", handle_automation_triggered),
        ]
        capture_data["active"] = True
        
        _LOGGER.warning(f"✅ CAPTURE STARTED for device {DEVICE_ID} (entity: {ENTITY_ID})")
        _LOGGER.warning(f"📝 Output file: {OUTPUT_FILE}")
        
        output = {"status": "started", "device_id": DEVICE_ID, "entity_id": ENTITY_ID, "output_file": str(OUTPUT_FILE)}

elif service == "capture_balcone_stop":
    if not capture_data.get("active", False):
        _LOGGER.warning("Capture not active")
        output = {"status": "not_active", "message": "Capture not running"}
    else:
        for unsub in capture_data.get("listeners", []):
            unsub()
        capture_data["listeners"] = []
        capture_data["active"] = False
        
        _LOGGER.warning("🛑 CAPTURE STOPPED")
        output = {"status": "stopped"}

elif service == "capture_balcone_status":
    output = {
        "active": capture_data.get("active", False),
        "device_id": DEVICE_ID,
        "entity_id": ENTITY_ID,
        "output_file": str(OUTPUT_FILE),
        "listeners_count": len(capture_data.get("listeners", []))
    }

else:
    output = {"error": f"Unknown service: {service}"}

# Set output for HA
output = output