"""Config flow for HA Clipboards."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class HAClipboardsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Clipboards."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        # Check if already configured
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="HA Clipboards", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "description": "HA Clipboards crea un'entità sensore per gestire più clipboard/testi con attributi dinamici."
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return HAClipboardsOptionsFlow(config_entry)


class HAClipboardsOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HA Clipboards."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )