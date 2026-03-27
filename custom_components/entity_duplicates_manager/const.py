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

EVENT_SCAN_COMPLETE = f"{DOMAIN}_scan_complete"

ATTR_ENTITY_ID = "entity_id"
ATTR_NEW_ENTITY_ID = "new_entity_id"
ATTR_DUPLICATES = "duplicates"
