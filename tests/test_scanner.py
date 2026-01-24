"""Test the duplicate scanner logic."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from custom_components.entity_duplicates_manager.scanner import DuplicatesScanner

async def test_scan_finds_duplicates(hass: HomeAssistant):
    """Test that the scanner identifies simple duplicates."""
    # Setup states
    hass.states.async_set("sensor.temp", "20")
    hass.states.async_set("sensor.temp_2", "21")
    hass.states.async_set("sensor.temp_3", "22")
    
    # unrelated
    hass.states.async_set("light.living_room", "on")

    scanner = DuplicatesScanner(hass)
    duplicates = scanner.scan(suffix_limit=5, exclude_patterns=[])

    assert len(duplicates) == 2
    # Check duplicate 1
    dup1 = next(d for d in duplicates if d["entity_id"] == "sensor.temp_2")
    assert dup1["base_entity"] == "sensor.temp"
    
    # Check duplicate 2
    dup2 = next(d for d in duplicates if d["entity_id"] == "sensor.temp_3")
    assert dup2["base_entity"] == "sensor.temp"

async def test_scan_respects_limit(hass: HomeAssistant):
    """Test suffix limit."""
    hass.states.async_set("sensor.temp", "20")
    hass.states.async_set("sensor.temp_2", "21")
    hass.states.async_set("sensor.temp_10", "22")

    scanner = DuplicatesScanner(hass)
    # Limit 5 should catch _2 but ignore _10
    # Note: Logic says suffix <= suffix_limit + 10. 
    # Let's check the code: "if suffix <= suffix_limit + 10:"
    # That means if limit is 2, it scans up to 12? 
    # Let's re-read scanner.py: "if suffix <= suffix_limit + 10:"
    # Yes, the scanner has a buffer. 
    
    # Let's test the limit logic strictly.
    # If I pass limit=2, 2+10=12. So _10 is included.
    # Let's try _50.
    hass.states.async_set("sensor.temp_50", "99")
    
    duplicates = scanner.scan(suffix_limit=2, exclude_patterns=[])
    
    # Should find temp_2 and temp_10 (2 <= 12, 10 <= 12)
    # But temp_50 (50 > 12) should be excluded.
    
    found_ids = [d["entity_id"] for d in duplicates]
    assert "sensor.temp_2" in found_ids
    assert "sensor.temp_10" in found_ids
    assert "sensor.temp_50" not in found_ids

async def test_scan_respects_exclude(hass: HomeAssistant):
    """Test exclude patterns."""
    hass.states.async_set("sensor.keep_me", "1")
    hass.states.async_set("sensor.keep_me_2", "1")
    hass.states.async_set("sensor.remove_me", "1")
    hass.states.async_set("sensor.remove_me_2", "1")

    scanner = DuplicatesScanner(hass)
    # Exclude strict match and wildcard
    duplicates = scanner.scan(suffix_limit=5, exclude_patterns=["sensor.keep_me*", "other.*"])

    found_ids = [d["entity_id"] for d in duplicates]
    assert "sensor.keep_me_2" not in found_ids
    assert "sensor.remove_me_2" in found_ids

async def test_fix_entity(hass: HomeAssistant):
    """Test renaming an entity."""
    scanner = DuplicatesScanner(hass)
    entity_registry = er.async_get(hass)
    
    # Create an entity in registry
    entry = entity_registry.async_get_or_create(
        "sensor", "test_platform", "unique_123", suggested_object_id="my_sensor_2"
    )
    assert entry.entity_id == "sensor.my_sensor_2"
    
    # Rename
    await scanner.async_fix_entity_id("sensor.my_sensor_2", "sensor.my_sensor_fixed")
    
    # Verify
    new_entry = entity_registry.async_get("sensor.my_sensor_fixed")
    assert new_entry is not None
    assert new_entry.unique_id == "unique_123"
    assert entity_registry.async_get("sensor.my_sensor_2") is None

async def test_delete_entity(hass: HomeAssistant):
    """Test deleting an entity."""
    scanner = DuplicatesScanner(hass)
    entity_registry = er.async_get(hass)
    
    entity_registry.async_get_or_create(
        "sensor", "test_platform", "unique_del", suggested_object_id="delete_me"
    )
    
    await scanner.async_delete_entity("sensor.delete_me")
    
    assert entity_registry.async_get("sensor.delete_me") is None
