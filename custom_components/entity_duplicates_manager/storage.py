"""Storage manager for Entity Duplicates Manager."""
import json
import os
import logging
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class StorageManager:
    """Handle persistence of settings and exclusions in /config directory."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the storage manager."""
        self.hass = hass
        # Persistent path outside custom_components
        self.dir_path = hass.config.path("entity_duplicates_manager")
        self.path = os.path.join(self.dir_path, "config.json")
        
        self._config = {
            "max_suffix": 9,
            "exclusion_patterns": "switch_%, input_boolean.sel_%",
            "excluded_entities": []
        }

    async def async_load(self):
        """Load config from file asynchronously."""
        def _load_sync():
            if os.path.exists(self.path):
                try:
                    with open(self.path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    _LOGGER.error("Error loading storage config file: %s", e)
            return None

        data = await self.hass.async_add_executor_job(_load_sync)
        if data:
            self._config.update(data)

    async def async_save(self, data: dict = None):
        """Save config to file asynchronously."""
        if data:
            # Handle list updates carefully
            for key, value in data.items():
                if key == "excluded_entities" and isinstance(value, list):
                    # For exclusions, we usually want to merge or replace. 
                    # The current logic in __init__ handles merging, so here we replace.
                    self._config[key] = value
                else:
                    self._config[key] = value
        
        def _save_sync():
            try:
                if not os.path.exists(self.dir_path):
                    os.makedirs(self.dir_path, exist_ok=True)
                
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=4)
                return True
            except Exception as e:
                _LOGGER.error("Error saving storage config: %s", e)
                return False

        await self.hass.async_add_executor_job(_save_sync)

    @property
    def config(self):
        """Return the current config."""
        return self._config
