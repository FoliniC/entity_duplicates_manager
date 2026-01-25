"""Scanner logic for identifying duplicate entities."""

import logging
import re
from typing import Optional
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import EVENT_SCAN_COMPLETE

_LOGGER = logging.getLogger(__name__)


class DuplicatesScanner:
    """Class to scan for duplicate entities."""

    def __init__(self, hass: HomeAssistant):
        """Initialize the scanner."""
        self.hass = hass
        self._duplicates = []

    def scan(self, suffix_limit: Optional[int], exclude_patterns: list[str]):
        """Scan for duplicates."""
        _LOGGER.info(f"Starting duplicate scan (limit={suffix_limit})...")
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

                # If suffix_limit is None or negative, we don't filter by suffix depth
                should_add = False
                if suffix_limit is None or suffix_limit < 0:
                    should_add = True
                elif suffix <= suffix_limit + 10:  # Original safety buffer
                    should_add = True

                if should_add:
                    if base_name not in candidates:
                        candidates[base_name] = []
                    candidates[base_name].append(state)

        found_duplicates = []

        for base_name, states in candidates.items():
            # Sort by suffix
            states.sort(key=lambda s: int(pattern.match(s.entity_id).group(2)))

            for state in states:
                entry = ent_reg.async_get(state.entity_id)
                unique_id = entry.unique_id if entry else "N/A"
                integration = entry.platform if entry else "N/A"

                found_duplicates.append(
                    {
                        "entity_id": state.entity_id,
                        "base_entity": base_name,
                        "state": state.state,
                        "friendly_name": state.attributes.get("friendly_name"),
                        "integration": integration,
                        "unique_id": unique_id,
                    }
                )

        self._duplicates = found_duplicates
        _LOGGER.info(
            f"Scan complete. Found {len(found_duplicates)} potential duplicates."
        )

        self.hass.bus.async_fire(
            EVENT_SCAN_COMPLETE,
            {"count": len(found_duplicates), "duplicates": found_duplicates},
        )
        return found_duplicates

    def _match_pattern(self, entity_id, pattern):
        """Simple wildcard matching."""
        # Convert simple wildcard to regex
        regex = pattern.replace(".", r"\.").replace("*", ".*")
        return re.match(f"^{regex}$", entity_id) is not None

    async def async_fix_entity_id(self, entity_id, new_entity_id):
        """Rename an entity and update attributes if necessary."""
        ent_reg = er.async_get(self.hass)
        entry = ent_reg.async_get(entity_id)

        if not entry:
            raise ValueError(f"Entity {entity_id} not found in registry.")

        current_state = self.hass.states.get(entity_id)
        current_name = entry.name or (current_state.attributes.get("friendly_name") if current_state else None)
        
        new_name = None
        if current_name:
            if entity_id in current_name:
                new_name = current_name.replace(entity_id, new_entity_id)
            
            suffix_match = re.search(r"(.+)[ _]([0-9]+)$", current_name)
            if suffix_match and not new_name:
                base_part = suffix_match.group(1).strip()
                new_name = base_part

        _LOGGER.info(f"Renaming {entity_id} to {new_entity_id} (New name: {new_name})")
        
        ent_reg.async_update_entity(
            entity_id, 
            new_entity_id=new_entity_id,
            name=new_name if new_name else entry.name
        )

    async def async_delete_entity(self, entity_id):
        """Delete an entity."""
        ent_reg = er.async_get(self.hass)
        if ent_reg.async_get(entity_id):
            _LOGGER.info(f"Removing {entity_id} from registry")
            ent_reg.async_remove(entity_id)
        else:
            self.hass.states.async_remove(entity_id)
