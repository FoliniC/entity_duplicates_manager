"""Test integration setup and services."""
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.entity_duplicates_manager.const import DOMAIN, SERVICE_SCAN

async def test_setup_entry_and_scan_service(hass: HomeAssistant):
    """Test setup and service call."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert "scanner" in hass.data[DOMAIN]

    # Verify entities are created
    state = hass.states.get("sensor.duplicates_found")
    assert state is not None
    assert state.state == "0"

    # Call service
    with patch("custom_components.entity_duplicates_manager.scanner.DuplicatesScanner.scan") as mock_scan:
        await hass.services.async_call(DOMAIN, SERVICE_SCAN, {}, blocking=True)
        mock_scan.assert_called_once()

    # Call fix service
    with patch("custom_components.entity_duplicates_manager.scanner.DuplicatesScanner.async_fix_entity_id") as mock_fix:
        await hass.services.async_call(DOMAIN, "fix_entity", {"entity_id": "a.b", "new_entity_id": "a.c"}, blocking=True)
        mock_fix.assert_called_once_with("a.b", "a.c")

    # Call delete service
    with patch("custom_components.entity_duplicates_manager.scanner.DuplicatesScanner.async_delete_entity") as mock_del:
        await hass.services.async_call(DOMAIN, "delete_entity", {"entity_id": "a.b"}, blocking=True)
        mock_del.assert_called_once_with("a.b")

    # Test unload
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN not in hass.data