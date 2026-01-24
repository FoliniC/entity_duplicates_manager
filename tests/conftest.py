"""Fixtures for Entity Duplicates Manager tests."""
import pytest
from custom_components.entity_duplicates_manager.const import DOMAIN

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield
