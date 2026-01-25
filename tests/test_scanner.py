"""Test the duplicate scanner logic."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from custom_components.entity_duplicates_manager.scanner import DuplicatesScanner

async def test_scan_finds_duplicates(hass: HomeAssistant):
    """Test that the scanner identifies simple duplicates."""
    hass.states.async_set("sensor.temp", "20")
    hass.states.async_set("sensor.temp_2", "21")
    
    scanner = DuplicatesScanner(hass)
    duplicates = scanner.scan(suffix_limit=5, exclude_patterns=[])
    assert len(duplicates) == 1

async def test_scan_respects_limit(hass: HomeAssistant):
    """Test suffix limit."""
    hass.states.async_set("sensor.temp", "20")
    hass.states.async_set("sensor.temp_50", "99")
    
    scanner = DuplicatesScanner(hass)
    duplicates = scanner.scan(suffix_limit=2, exclude_patterns=[])
    found_ids = [d["entity_id"] for d in duplicates]
    assert "sensor.temp_50" not in found_ids

async def test_scan_no_limit(hass: HomeAssistant):
    """Test scan with no suffix limit."""
    hass.states.async_set("sensor.temp_99", "99")
    scanner = DuplicatesScanner(hass)
    # limit None should find it
    duplicates = scanner.scan(suffix_limit=None, exclude_patterns=[])
    assert any(d["entity_id"] == "sensor.temp_99" for d in duplicates)

async def test_scan_respects_exclude(hass: HomeAssistant):
    """Test exclude patterns."""
    hass.states.async_set("sensor.keep_me_2", "1")
    scanner = DuplicatesScanner(hass)
    duplicates = scanner.scan(suffix_limit=5, exclude_patterns=["sensor.keep_me*"])
    assert len(duplicates) == 0

async def test_fix_entity_with_name_update(hass: HomeAssistant):
    """Test renaming an entity and its friendly name."""
    scanner = DuplicatesScanner(hass)
    entity_registry = er.async_get(hass)
    
    entry = entity_registry.async_get_or_create(
        "sensor", "test_platform", "unique_123", 
        suggested_object_id="my_sensor_2"
    )
    entity_id = entry.entity_id
    
    # Set the state with friendly name
    hass.states.async_set(entity_id, "20", {"friendly_name": "My Sensor 2"})
    
    # Rename
    await scanner.async_fix_entity_id(entity_id, "sensor.my_sensor")
    
    new_entry = entity_registry.async_get("sensor.my_sensor")
    assert new_entry is not None
    # The logic in scanner.py should have cleaned "My Sensor 2" to "My Sensor"
    assert new_entry.name == "My Sensor"

async def test_delete_entity(hass: HomeAssistant):
    """Test deleting an entity."""
    scanner = DuplicatesScanner(hass)
    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create("sensor", "test_platform", "u", suggested_object_id="del")
    await scanner.async_delete_entity("sensor.del")
    assert entity_registry.async_get("sensor.del") is None
