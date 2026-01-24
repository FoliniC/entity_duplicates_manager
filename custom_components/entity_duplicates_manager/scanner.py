"""Scanner logic for identifying duplicate entities."""
import logging
import re
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, EVENT_SCAN_COMPLETE

_LOGGER = logging.getLogger(__name__)

class DuplicatesScanner:
    """Class to scan for duplicate entities."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the scanner."""
        self.hass = hass
        self._duplicates = []

    def scan(self, suffix_limit: int, exclude_patterns: list[str]):
        """Scan for duplicates."""
        _LOGGER.info("Starting duplicate scan...")
        all_states = self.hass.states.async_all()
        ent_reg = er.async_get(self.hass)
        
        # Simple heuristic: Look for _2, _3, etc. at the end of entity_ids
        pattern = re.compile(r"(.+)_([0-9]+)$")
        
        candidates = {}

        for state in all_states:
            entity_id = state.entity_id
            
            # Check exclusions
            if any(self._match_pattern(entity_id, pat) for pat in exclude_patterns):
                continue

            match = pattern.match(entity_id)
            if match:
                base_name = match.group(1)
                suffix = int(match.group(2))
                
                if suffix <= suffix_limit + 10: # Look a bit beyond to be safe
                    if base_name not in candidates:
                        candidates[base_name] = []
                    candidates[base_name].append(state)

        found_duplicates = []

        for base_name, states in candidates.items():
            # Check if the "original" exists (without suffix or with _1)
            # This is a simplified logic. In a real scenario, we'd check registry details.
            original = self.hass.states.get(base_name)
            
            # Sort by suffix
            states.sort(key=lambda s: int(pattern.match(s.entity_id).group(2)))
            
            for state in states:
                 entry = ent_reg.async_get(state.entity_id)
                 unique_id = entry.unique_id if entry else "N/A"
                 integration = entry.platform if entry else "N/A"
                 
                 found_duplicates.append({
                     "entity_id": state.entity_id,
                     "base_entity": base_name,
                     "state": state.state,
                     "friendly_name": state.attributes.get("friendly_name"),
                     "integration": integration,
                     "unique_id": unique_id
                 })

        self._duplicates = found_duplicates
        _LOGGER.info(f"Scan complete. Found {len(found_duplicates)} potential duplicates.")
        
        self.hass.bus.async_fire(EVENT_SCAN_COMPLETE, {"count": len(found_duplicates), "duplicates": found_duplicates})
        return found_duplicates

    def _match_pattern(self, entity_id, pattern):
        """Simple wildcard matching."""
        # Convert simple wildcard to regex
        regex = pattern.replace(".", "\.").replace("*", ".*")
        return re.match(f"^{regex}$", entity_id) is not None

    async def async_fix_entity_id(self, entity_id, new_entity_id):
        """Rename an entity."""
        ent_reg = er.async_get(self.hass)
        entry = ent_reg.async_get(entity_id)
        
        if not entry:
            raise ValueError(f"Entity {entity_id} not found in registry.")
            
        _LOGGER.info(f"Renaming {entity_id} to {new_entity_id}")
        ent_reg.async_update_entity(entity_id, new_entity_id=new_entity_id)

    async def async_delete_entity(self, entity_id):
        """Delete an entity."""
        ent_reg = er.async_get(self.hass)
        if ent_reg.async_get(entity_id):
             _LOGGER.info(f"Removing {entity_id} from registry")
             ent_reg.async_remove(entity_id)
        else:
            # Maybe it's just a state without registry entry?
            self.hass.states.async_remove(entity_id)
