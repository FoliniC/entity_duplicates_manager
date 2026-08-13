"""Scanner logic for identifying duplicate entities."""

import json
import logging
import re
from typing import Optional
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import EVENT_SCAN_COMPLETE

_LOGGER = logging.getLogger(__name__)
MAX_EVENT_DATA_BYTES = 30000


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

        configured_limit = self._get_config_limit()
        _LOGGER.info("Configured duplicate limit: %s", configured_limit)

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

                new_attrs = None

                # Mark entities not in registry (from states only)
                if not entry:
                    if state.attributes.get("friendly_name"):
                        # Create new attrs dict since state.attributes is ReadOnlyDict
                        new_attrs = dict(state.attributes)
                        new_attrs["friendly_name"] = (
                            state.attributes["friendly_name"] + " (from states)"
                        )
                else:
                    new_attrs = None

                found_duplicates.append(
                    {
                        "entity_id": state.entity_id,
                        "base_entity": base_name,
                        "state": state.state,
                        "friendly_name": new_attrs["friendly_name"]
                        if new_attrs
                        else state.attributes.get("friendly_name"),
                        "integration": integration,
                        "unique_id": unique_id,
                        "in_registry": entry is not None,
                        "source": "registry" if entry else "states",
                        "can_rename": entry is not None,
                    }
                )

        self._duplicates = found_duplicates

        self.fire_scan_complete(found_duplicates)
        return found_duplicates

    def _get_config_limit(self) -> int:
        """Get configured limit from input_number entity."""
        try:
            entity_id = "input_number.entity_duplicates_manager_limit"
            state = self.hass.states.get(entity_id)
            if state and state.state not in ("unknown", "unavailable", ""):
                limit = int(state.state)
                if 50 <= limit <= 500:  # Reasonable range
                    return limit
            return 100  # Default fallback
        except Exception:
            return 100  # Default fallback

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
            _LOGGER.warning(
                "Entity %s exists in states but not in the entity registry; "
                "it cannot be renamed through the entity registry.",
                entity_id,
            )
            return False

        current_state = self.hass.states.get(entity_id)
        current_name = entry.name or (
            current_state.attributes.get("friendly_name") if current_state else None
        )

        new_name = None
        if current_name:
            if entity_id in current_name:
                new_name = current_name.replace(entity_id, new_entity_id)

            suffix_match = re.search(r"(.+)[ _]([0-9]+)$", current_name)
            if suffix_match and not new_name:
                base_part = suffix_match.group(1).strip()
                new_name = base_part

        _LOGGER.info("Renaming %s to %s (New name: %s)", entity_id, new_entity_id, new_name)

        # Check if target entity already exists
        existing_entry = ent_reg.async_get(new_entity_id)
        if existing_entry:
            _LOGGER.warning(
                "Target entity %s already exists. Purging statistics and removing "
                "base entity before promoting duplicate.",
                new_entity_id,
            )
            # First, purge statistics for the base entity to avoid recorder migration conflicts
            try:
                await self.hass.services.async_call(
                    "recorder",
                    "purge_entities",
                    {"entity_ids": [new_entity_id]},
                    blocking=True,
                )
                _LOGGER.info("Purged statistics for %s", new_entity_id)
            except Exception as err:
                _LOGGER.warning("Could not purge statistics for %s: %s", new_entity_id, err)

            # Remove the base entity from registry
            ent_reg.async_remove(new_entity_id)
            # Also remove its state
            self.hass.states.async_remove(new_entity_id)

        # Now rename the duplicate to the base name
        ent_reg.async_update_entity(
            entity_id,
            new_entity_id=new_entity_id,
            name=new_name if new_name else entry.name,
        )
        return True

    async def async_delete_entity(self, entity_id):
        """Delete an entity."""
        ent_reg = er.async_get(self.hass)
        if ent_reg.async_get(entity_id):
            _LOGGER.info("Removing %s from registry", entity_id)
            ent_reg.async_remove(entity_id)
        else:
            self.hass.states.async_remove(entity_id)

    def fire_scan_complete(self, duplicates: list[dict], config: dict | None = None) -> None:
        """Fire scan complete event with bounded payload size."""
        payload = self._build_scan_complete_payload(duplicates, config)
        self.hass.bus.async_fire(EVENT_SCAN_COMPLETE, payload)
        _LOGGER.info(
            "Fired %s event with %s total entities, %s entities in payload (%s bytes)",
            EVENT_SCAN_COMPLETE,
            payload["count"],
            payload["stored_count"],
            payload["event_data_bytes"],
        )

    def _build_scan_complete_payload(
        self, duplicates: list[dict], config: dict | None = None
    ) -> dict:
        """Build scan event data within Recorder event size limits."""
        configured_limit = self._get_config_limit()
        _LOGGER.info("Configured duplicate limit: %s", configured_limit)

        safe_config = self._safe_event_config(config)
        duplicates_to_store = [
            self._safe_event_duplicate(duplicate)
            for duplicate in duplicates[:configured_limit]
        ]

        payload = {
            "count": len(duplicates),
            "duplicates": duplicates_to_store,
            "stored_count": len(duplicates_to_store),
            "configured_limit": configured_limit,
            "limit_applied": len(duplicates) > len(duplicates_to_store),
            "payload_truncated": False,
        }
        if safe_config is not None:
            payload["config"] = safe_config

        while duplicates_to_store and self._event_data_size(payload) > MAX_EVENT_DATA_BYTES:
            duplicates_to_store.pop()
            payload["stored_count"] = len(duplicates_to_store)
            payload["limit_applied"] = True
            payload["payload_truncated"] = True

        payload["event_data_bytes"] = self._event_data_size(payload)

        _LOGGER.info(
            "Scan complete. Found %s potential duplicates, storing first %s in UI",
            len(duplicates),
            len(duplicates_to_store),
        )

        return payload

    def _safe_event_duplicate(self, duplicate: dict) -> dict:
        """Keep only fields needed by the UI event payload."""
        return {
            "entity_id": duplicate.get("entity_id"),
            "base_entity": duplicate.get("base_entity"),
            "friendly_name": duplicate.get("friendly_name"),
            "in_registry": duplicate.get("in_registry", True),
            "source": duplicate.get("source", "registry"),
            "can_rename": duplicate.get("can_rename", True),
        }

    def _safe_event_config(self, config: dict | None) -> dict | None:
        """Keep config payload small enough for Recorder."""
        if config is None:
            return None

        return {
            "max_suffix": config.get("max_suffix"),
            "exclusion_patterns": config.get("exclusion_patterns", ""),
            "excluded_entities_count": len(config.get("excluded_entities", [])),
        }

    def _event_data_size(self, payload: dict) -> int:
        """Return approximate serialized event data size in bytes."""
        return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))
