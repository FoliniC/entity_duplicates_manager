"""Test the entity platforms."""
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry, mock_restore_cache
from custom_components.entity_duplicates_manager.const import DOMAIN

async def test_number_platform(hass: HomeAssistant):
    """Test the number entity."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    
    # Test restore state
    mock_restore_cache(hass, (
        State("number.suffix_filter_max", "7.0"),
    ))

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Check restored state
    state = hass.states.get("number.suffix_filter_max")
    assert state.state == "7.0"

    # Check update
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": "number.suffix_filter_max", "value": 3},
        blocking=True
    )
    
    state = hass.states.get("number.suffix_filter_max")
    assert state.state == "3.0"
    
    # Test bad restore value logic (implicit coverage)
    # We would need to reload to test bad restore.

async def test_text_platform(hass: HomeAssistant):
    """Test the text entity."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    
    mock_restore_cache(hass, (
        State("text.exclude_patterns", "a,b,c"),
    ))

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("text.exclude_patterns")
    assert state.state == "a,b,c"

    await hass.services.async_call(
        "text", "set_value",
        {"entity_id": "text.exclude_patterns", "value": "x,y"},
        blocking=True
    )
    
    state = hass.states.get("text.exclude_patterns")
    assert state.state == "x,y"

async def test_switch_platform(hass: HomeAssistant):
    """Test the switch entity."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    
    mock_restore_cache(hass, (
        State("switch.confirm_deletion", "on"),
    ))

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("switch.confirm_deletion")
    assert state.state == "on"

    await hass.services.async_call(
        "switch", "turn_off",
        {"entity_id": "switch.confirm_deletion"},
        blocking=True
    )
    
    state = hass.states.get("switch.confirm_deletion")
    assert state.state == "off"
    
    await hass.services.async_call(
        "switch", "turn_on",
        {"entity_id": "switch.confirm_deletion"},
        blocking=True
    )
    state = hass.states.get("switch.confirm_deletion")
    assert state.state == "on"

async def test_sensor_platform(hass: HomeAssistant):
    """Test the sensor entity."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    
    mock_restore_cache(hass, (
        State("sensor.duplicates_found", "10"),
    ))

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.duplicates_found")
    assert state.state == "10"
