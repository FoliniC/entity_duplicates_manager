#!/usr/bin/env python3
"""
Capture script for LocalTuya device messages.
Captures all messages for the balcony device (bfbf8ab6b500e77408pupf) 
to understand why it turns on unexpectedly.

This script connects to Home Assistant via WebSocket and subscribes to:
1. LocalTuya dispatcher signals: localtuya_{device_id}
2. HA events: localtuya_status_update, localtuya_device_dp_triggered
3. State changes for switch.luce_balcone_switch_1

Output is written to a JSONL file for analysis.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import aiohttp

# Configuration
HA_URL = "http://192.168.0.3:8123"  # Home Assistant URL
HA_TOKEN = None  # Will read from .env or prompt
DEVICE_ID = "bfbf8ab6b500e77408pupf"
ENTITY_ID = "switch.luce_balcone_switch_1"
OUTPUT_FILE = Path("/home/carlo/docker/homeassistant/config/logs/balcone_capture.jsonl")
LOG_LEVEL = logging.INFO

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_LOGGER = logging.getLogger("balcone_capture")


class BalconeCapture:
    def __init__(self, ha_url: str, token: str, output_file: Path):
        self.ha_url = ha_url.rstrip("/")
        self.token = token
        self.output_file = output_file
        self.session = None
        self.ws = None
        self.msg_id = 1
        self.running = False
        self.subscriptions = set()

    async def connect(self):
        """Connect to Home Assistant WebSocket."""
        self.session = aiohttp.ClientSession()
        ws_url = f"{self.ha_url.replace('http', 'ws')}/api/websocket"
        
        _LOGGER.info(f"Connecting to {ws_url}")
        self.ws = await self.session.ws_connect(ws_url)
        
        # Authenticate
        auth_msg = await self.ws.receive_json()
        if auth_msg.get("type") != "auth_required":
            raise Exception(f"Expected auth_required, got {auth_msg}")
        
        await self.ws.send_json({
            "type": "auth",
            "access_token": self.token
        })
        
        auth_result = await self.ws.receive_json()
        if auth_result.get("type") != "auth_ok":
            raise Exception(f"Authentication failed: {auth_result}")
        
        _LOGGER.info("Authenticated successfully")
        self.running = True

    async def send_command(self, command: dict):
        """Send a command over WebSocket."""
        command["id"] = self.msg_id
        self.msg_id += 1
        await self.ws.send_json(command)

    async def subscribe_events(self):
        """Subscribe to relevant events."""
        # Subscribe to LocalTuya status_update events
        await self.send_command({
            "type": "subscribe_events",
            "event_type": "localtuya_status_update"
        })
        self.subscriptions.add("localtuya_status_update")
        
        # Subscribe to LocalTuya device_dp_triggered events
        await self.send_command({
            "type": "subscribe_events",
            "event_type": "localtuya_device_dp_triggered"
        })
        self.subscriptions.add("localtuya_device_dp_triggered")
        
        # Subscribe to state changes for the balcony switch
        await self.send_command({
            "type": "subscribe_events",
            "event_type": "state_changed",
            "entity_id": ENTITY_ID
        })
        self.subscriptions.add(f"state_changed:{ENTITY_ID}")
        
        # Subscribe to automation triggers (for anti-accensione)
        await self.send_command({
            "type": "subscribe_events",
            "event_type": "automation_triggered",
            "entity_id": "automation.anti_accensione_balcone"
        })
        self.subscriptions.add("automation_triggered:anti_accensione_balcone")
        
        _LOGGER.info(f"Subscribed to events: {self.subscriptions}")

    def write_event(self, event_type: str, data: dict):
        """Write event to JSONL file."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        with open(self.output_file, "a") as f:
            f.write(json.dumps(record) + "\n")

    async def handle_message(self, msg):
        """Handle incoming WebSocket message."""
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = msg.json()
            msg_type = data.get("type")
            
            if msg_type == "event":
                event = data.get("event", {})
                event_type = event.get("event_type")
                event_data = event.get("data", {})
                
                # Filter for our device
                if event_type in ("localtuya_status_update", "localtuya_device_dp_triggered"):
                    device_id = event_data.get("device_id")
                    if device_id == DEVICE_ID:
                        self.write_event(event_type, event_data)
                        _LOGGER.info(f"[{event_type}] Device: {device_id}, Data: {event_data}")
                
                elif event_type == "state_changed":
                    entity_id = event_data.get("entity_id")
                    if entity_id == ENTITY_ID:
                        self.write_event("state_changed", event_data)
                        _LOGGER.info(f"[state_changed] Entity: {entity_id}, New: {event_data.get('new_state')}, Old: {event_data.get('old_state')}")
                
                elif event_type == "automation_triggered":
                    self.write_event("automation_triggered", event_data)
                    _LOGGER.info(f"[automation_triggered] {event_data}")
            
            elif msg_type == "result":
                if not data.get("success"):
                    _LOGGER.warning(f"Command failed: {data}")
            
            elif msg_type == "pong":
                pass  # Heartbeat
        
        elif msg.type == aiohttp.WSMsgType.ERROR:
            _LOGGER.error(f"WebSocket error: {self.ws.exception()}")

    async def run(self):
        """Main run loop."""
        await self.connect()
        await self.subscribe_events()
        
        _LOGGER.info(f"Capturing messages for device {DEVICE_ID} (entity: {ENTITY_ID})")
        _LOGGER.info(f"Output file: {self.output_file}")
        _LOGGER.info("Press Ctrl+C to stop")
        
        try:
            async for msg in self.ws:
                await self.handle_message(msg)
        except KeyboardInterrupt:
            _LOGGER.info("Stopping capture...")
        except Exception as e:
            _LOGGER.error(f"Error in capture loop: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up connections."""
        self.running = False
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        _LOGGER.info("Capture stopped")


async def get_token():
    """Get HA token from .env or prompt."""
    import os
    from pathlib import Path
    
    # Try .env file
    env_path = Path("/home/carlo/docker/homeassistant/config/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("HA_TOKEN=") or line.startswith("SUPERVISOR_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"')
    
    # Try supervisor token
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
    if supervisor_token:
        return supervisor_token
    
    # Prompt
    return input("Enter Home Assistant Long-Lived Access Token: ").strip()


async def main():
    """Main entry point."""
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear or create output file
    if OUTPUT_FILE.exists():
        backup = OUTPUT_FILE.with_suffix(f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
        OUTPUT_FILE.rename(backup)
        _LOGGER.info(f"Previous capture backed up to {backup}")
    
    token = await get_token()
    if not token:
        _LOGGER.error("No token provided")
        sys.exit(1)
    
    capture = BalconeCapture(HA_URL, token, OUTPUT_FILE)
    await capture.run()


if __name__ == "__main__":
    asyncio.run(main())