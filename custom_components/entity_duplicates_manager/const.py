"""Constants for the Entity Duplicates Manager integration."""

DOMAIN = "entity_duplicates_manager"

CONF_SUFFIX_MAX = "suffix_max"
CONF_EXCLUDE_PATTERN = "exclude_pattern"
CONF_CONFIRM_DELETION = "confirm_deletion"

DEFAULT_SUFFIX_MAX = 2
DEFAULT_EXCLUDE_PATTERN = "sensor.uptime*, group.*"

SERVICE_SCAN = "scan_duplicates"
SERVICE_FIX = "fix_entity"
SERVICE_DELETE = "delete_entity"
SERVICE_RENAME = "rename_entities_to_base"

EVENT_SCAN_COMPLETE = f"{DOMAIN}_scan_complete"
EVENT_DELETE_COMPLETE = f"{DOMAIN}_delete_complete"