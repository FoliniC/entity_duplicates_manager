"""Test integration setup and services."""
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.entity_duplicates_manager.const import DOMAIN, SERVICE_SCAN

async def test_setup_entry_and_scan_service(hass: HomeAssistant):
    """Test setup and service call."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    
    # Mocking storage load to avoid actual IO
    with patch("custom_components.entity_duplicates_manager.storage.StorageManager.async_load", return_value=None):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert DOMAIN in hass.data
    assert "scanner" in hass.data[DOMAIN]
    assert "storage" in hass.data[DOMAIN]

    # Verify entities are created
    state = hass.states.get("sensor.duplicates_found")
    assert state is not None

    # Call scan service
    with patch("custom_components.entity_duplicates_manager.scanner.DuplicatesScanner.scan", return_value=[]) as mock_scan:
        await hass.services.async_call(DOMAIN, SERVICE_SCAN, {}, blocking=True)
        mock_scan.assert_called_once()

    # Call save_settings service
    with patch("custom_components.entity_duplicates_manager.storage.StorageManager.async_save") as mock_save:
        await hass.services.async_call(DOMAIN, "save_settings", {"max_suffix": 5, "exclusion_patterns": "a,b"}, blocking=True)
        mock_save.assert_called_once()

    # Call exclude_entities service
    with patch("custom_components.entity_duplicates_manager.storage.StorageManager.async_save") as mock_save_exc:
        await hass.services.async_call(DOMAIN, "exclude_entities", {"entity_ids": ["light.test"]}, blocking=True)
        mock_save_exc.assert_called_once()

    # Call delete_entities service (bulk)
    with patch("custom_components.entity_duplicates_manager.scanner.DuplicatesScanner.async_delete_entity") as mock_del:
        await hass.services.async_call(DOMAIN, "delete_entities", {"entity_ids": ["light.a", "light.b"]}, blocking=True)
        assert mock_del.call_count == 2

    # Call rename_entities_to_base service
    with patch("custom_components.entity_duplicates_manager.scanner.DuplicatesScanner.async_fix_entity_id") as mock_fix:
        # Pre-fill scanner with some fake data so it finds the match
        hass.data[DOMAIN]["scanner"]._duplicates = [{"entity_id": "light.a_2", "base_entity": "light.a"}]
        await hass.services.async_call(DOMAIN, "rename_entities_to_base", {"entity_ids": ["light.a_2"]}, blocking=True)
        mock_fix.assert_called_once_with("light.a_2", "light.a")

    # Test unload
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN not in hass.data
