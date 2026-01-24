"""Test the config flow."""
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from custom_components.entity_duplicates_manager.const import DOMAIN

async def test_config_flow_success(hass: HomeAssistant):
    """Test we get the form and create the entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Entity Duplicates Manager"
    assert result2["data"] == {}

async def test_single_instance(hass: HomeAssistant):
    """Test we only allow one instance."""
    # Create one
    await _create_mock_entry(hass)
    
    # Try to create another
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"

async def _create_mock_entry(hass):
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    return entry
