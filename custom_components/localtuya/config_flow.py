"""Config flow for LocalTuya integration integration."""

import asyncio
import errno
import json
import logging
import time
import copy
from importlib import import_module
from functools import partial
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any


import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectOptionDict,
)
import voluptuous as vol
from homeassistant import exceptions
from homeassistant.core import callback, HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_ENTITIES,
    CONF_FRIENDLY_NAME,
    CONF_ENTITY_CATEGORY,
    CONF_HOST,
    CONF_ICON,
    CONF_ID,
    CONF_NAME,
    CONF_PLATFORM,
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_USERNAME,
    EntityCategory,
)

from .coordinator import HassLocalTuyaData
from .core import pytuya
from .core.cloud_api import TUYA_ENDPOINTS, TuyaCloudApi
from .core.helpers import templates, get_gateway_by_deviceid, gen_localtuya_entities
from .const import (
    ATTR_UPDATED_AT,
    CONF_ADD_DEVICE,
    CONF_CONFIGURE_CLOUD,
    CONF_DPS_STRINGS,
    CONF_DOWNLOAD_CLOUD_INFO,
    CONF_EDIT_DEVICE,
    CONF_ENABLE_ADD_ENTITIES,
    CONF_ENABLE_DEBUG,
    CONF_GATEWAY_ID,
    CONF_LOCAL_KEY,
    CONF_MANAGE_NETWORK,
    CONF_MAC_RETRIEVAL,
    CONF_MANUAL_DPS,
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    CONF_MODEL,
    CONF_NODE_ID,
    CONF_NO_CLOUD,
    CONF_OPTIONS,
    CONF_PRODUCT_KEY,
    CONF_PRODUCT_NAME,
    CONF_PROTOCOL_VERSION,
    CONF_RESET_DPIDS,
    CONF_SCALING,
    CONF_STATE_CLASS,
    CONF_STEPSIZE,
    CONF_TUYA_GWID,
    CONF_TUYA_IP,
    CONF_TUYA_VERSION,
    CONF_USER_ID,
    CONF_MAC,
    DATA_DISCOVERY,
    DEFAULT_CATEGORIES,
    DOMAIN,
    ENTITY_CATEGORY,
    PLATFORMS,
    SUPPORTED_PROTOCOL_VERSIONS,
    CONF_DEVICE_SLEEP_TIME,
)
from .discovery import discover

_LOGGER = logging.getLogger(__name__)

ENTRIES_VERSION = 4

PLATFORM_TO_ADD = "platform_to_add"
USE_TEMPLATE = "use_template"
TEMPLATES = "templates"
NO_ADDITIONAL_ENTITIES = "no_additional_entities"
SELECTED_DEVICE = "selected_device"
EXPORT_CONFIG = "export_config"

TUYA_CATEGORY = "category"
DEVICE_CLOUD_DATA = "device_cloud_data"

# Using list method so we can translate options.
CONFIGURE_MENU = [CONF_ADD_DEVICE, CONF_EDIT_DEVICE, CONF_CONFIGURE_CLOUD, CONF_MANAGE_NETWORK]

_LOGGER.debug("[TRACER] Config flow file loaded")


def _redact_log_input(user_input):
    """Return config-flow input with secrets masked for logs."""
    if not isinstance(user_input, dict):
        return user_input
    redacted = dict(user_input)
    for key in (CONF_LOCAL_KEY, CONF_CLIENT_SECRET, CONF_CLIENT_ID):
        if redacted.get(key):
            redacted[key] = "***"
    return redacted


def _cloud_func_values(func: dict[str, Any]) -> dict[str, Any]:
    """Return parsed Tuya cloud values/typeSpec metadata."""
    values = (func or {}).get("values")
    if isinstance(values, dict):
        return values
    if not isinstance(values, str) or not values:
        return {}
    try:
        return json.loads(values)
    except (TypeError, ValueError):
        return {}


def _cloud_value_scale(values: dict[str, Any]) -> float | None:
    """Return LocalTuya scale factor from Tuya decimal scale."""
    if "scale" not in values:
        return None
    try:
        return 1 / (10 ** int(values["scale"]))
    except (TypeError, ValueError):
        return None


def _cloud_unit(values: dict[str, Any]) -> str | None:
    """Return a Home Assistant friendly unit from Tuya metadata."""
    unit = values.get("unit")
    if unit is None:
        return None

    unit_str = str(unit).strip()
    if not unit_str:
        return None

    normalized = unit_str.lower().replace(" ", "")
    if normalized in {"kwh", "kw.h", "kw*h", "kw-h", "kw\u00b7h"}:
        return "kWh"
    if normalized == "mah":
        return "mAh"
    if normalized == "ma":
        return "mA"
    if normalized == "hz":
        return "Hz"
    if normalized == "v":
        return "V"
    if normalized == "w":
        return "W"
    if normalized == "kw":
        return "kW"
    if normalized in {"s", "sec", "second", "seconds"}:
        return "s"
    return unit_str


def _platform_value(platform: Any) -> str:
    """Return the string value of a HA Platform enum or plain platform."""
    return str(getattr(platform, "value", platform))


def _cloud_func_access_mode(func: dict[str, Any]) -> str:
    return str((func or {}).get("accessMode") or "").lower()


def _cloud_func_type(func: dict[str, Any]) -> str:
    return str(_cloud_func_values(func).get("type") or "").lower()


def _humanize_cloud_code(code: str) -> str:
    if not code:
        return ""
    return code.replace("_", " ").strip().title()


def _cloud_friendly_name(dp_id: str, func: dict[str, Any]) -> str:
    code = str((func or {}).get("code") or "")
    name = str((func or {}).get("name") or "")
    return _humanize_cloud_code(code) or name or f"DP {dp_id}"


def _cloud_sensor_device_class(code: str, unit: str | None) -> str | None:
    code_l = code.lower()
    unit_l = (unit or "").lower()

    if "energy" in code_l or unit_l == "kwh":
        return "energy"
    if (
        ("power" in code_l and "factor" not in code_l and "alarm" not in code_l)
        or unit_l in {"w", "kw"}
    ):
        return "power"
    if "current" in code_l or unit_l in {"a", "ma"}:
        return "current"
    if "voltage" in code_l or code_l.endswith("_v") or unit_l == "v":
        return "voltage"
    return None


def _cloud_sensor_state_class(code: str, device_class: str | None) -> str | None:
    if device_class == "energy" and "total" in code.lower():
        return "total_increasing"
    if device_class in {"current", "power", "voltage"}:
        return "measurement"
    return None


def _infer_cloud_platform(func: dict[str, Any]) -> str:
    """Infer a LocalTuya platform from Tuya cloud function metadata."""
    code = str((func or {}).get("code") or "").lower()
    access_mode = _cloud_func_access_mode(func)
    value_type = _cloud_func_type(func)

    if code.startswith("switch") or code in {"switch", "switch_all"}:
        return "switch"
    if code.startswith("alarm") or code.startswith("fault") or "_alarm" in code:
        return "binary_sensor"
    if value_type in {"bool", "boolean"}:
        return "switch" if "w" in access_mode and access_mode != "ro" else "binary_sensor"
    if value_type == "enum":
        return "select" if "w" in access_mode and access_mode != "ro" else "sensor"
    if value_type in {"integer", "value"}:
        sensor_terms = (
            "current",
            "energy",
            "freq",
            "power",
            "voltage",
        )
        config_terms = ("calibration", "control", "rate", "setting")
        if any(term in code for term in config_terms):
            return "number"
        if any(term in code for term in sensor_terms):
            return "sensor"
        if not access_mode:
            return "number"
        return "number" if "w" in access_mode and access_mode != "ro" else "sensor"
    return "sensor"


def _enrich_cloud_entity(entity: dict[str, Any], func: dict[str, Any]) -> dict[str, Any]:
    """Apply cloud typeSpec metadata to an auto-generated LocalTuya entity."""
    values = _cloud_func_values(func)
    value_type = str(values.get("type") or "").lower()
    platform = _platform_value(entity.get(CONF_PLATFORM))
    code = str((func or {}).get("code") or "")

    if platform in {"sensor", "number"} and value_type in {"integer", "value"}:
        if (scale_factor := _cloud_value_scale(values)) is not None:
            entity[CONF_SCALING] = scale_factor
        if unit := _cloud_unit(values):
            entity[CONF_UNIT_OF_MEASUREMENT] = unit

    if platform == "sensor":
        unit = entity.get(CONF_UNIT_OF_MEASUREMENT) or _cloud_unit(values)
        device_class = _cloud_sensor_device_class(code, unit)
        if device_class and not entity.get(CONF_DEVICE_CLASS):
            entity[CONF_DEVICE_CLASS] = device_class
        if state_class := _cloud_sensor_state_class(code, entity.get(CONF_DEVICE_CLASS)):
            entity.setdefault(CONF_STATE_CLASS, state_class)
        elif value_type in {"integer", "value"}:
            entity.setdefault(CONF_STATE_CLASS, "measurement")

    if platform == "number" and value_type in {"integer", "value"}:
        code_l = code.lower()
        if any(term in code_l for term in ("calibration", "control", "rate", "setting")):
            entity.setdefault(CONF_ENTITY_CATEGORY, EntityCategory.CONFIG)
        for source_key, target_key in (
            ("min", CONF_MIN_VALUE),
            ("max", CONF_MAX_VALUE),
            ("step", CONF_STEPSIZE),
        ):
            if source_key in values and values[source_key] is not None:
                entity[target_key] = values[source_key]

    if platform == "select" and value_type == "enum":
        range_values = values.get("range")
        if isinstance(range_values, list) and range_values:
            entity.setdefault(CONF_OPTIONS, {str(v): str(v) for v in range_values})

    if platform == "binary_sensor":
        code_l = code.lower()
        if (
            code_l.startswith("alarm")
            or code_l.startswith("fault")
            or "_alarm" in code_l
        ):
            entity.setdefault(CONF_DEVICE_CLASS, "problem")

    return entity


def _cloud_entity_from_func(dp_id: str, func: dict[str, Any]) -> dict[str, Any]:
    """Create a generic LocalTuya entity from Tuya cloud metadata."""
    entity: dict[str, Any] = {
        CONF_ID: int(dp_id),
        CONF_PLATFORM: _infer_cloud_platform(func),
        CONF_FRIENDLY_NAME: _cloud_friendly_name(dp_id, func),
    }
    return _enrich_cloud_entity(entity, func)


def _merge_cloud_entities(
    dev_data: list[dict[str, Any]] | None,
    cloud_funcs: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """Enrich generated entities and add any cloud DP not represented locally."""
    entities = list(dev_data or [])
    existing_by_id: dict[str, dict[str, Any]] = {
        str(entity.get(CONF_ID)): entity
        for entity in entities
        if isinstance(entity, dict) and entity.get(CONF_ID) is not None
    }

    for dp_id, entity in existing_by_id.items():
        if func := cloud_funcs.get(dp_id):
            _enrich_cloud_entity(entity, func if isinstance(func, dict) else {})

    forced_entities = 0
    for dp_id, func in cloud_funcs.items():
        dp_str = str(dp_id)
        if not dp_str.isdigit() or dp_str in existing_by_id:
            continue

        entity = _cloud_entity_from_func(dp_str, func if isinstance(func, dict) else {})
        entities.append(entity)
        existing_by_id[dp_str] = entity
        forced_entities += 1

    return entities, forced_entities

def col_to_select(
    opt_list: dict | list, multi_select=False, is_dps=False, custom_value=False
) -> SelectSelector:
    """Convert collections to SelectSelectorConfig."""
    if type(opt_list) == dict:
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=str(v), label=k) for k, v in opt_list.items()
                ],
                mode=SelectSelectorMode.DROPDOWN,
                custom_value=custom_value,
                multiple=True if multi_select else False,
            )
        )
    elif type(opt_list) == list:
        # value used the same method as func available_dps_string, no spaces values.
        return SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(
                        value=str(kv).split(" ")[0] if is_dps else str(kv),
                        label=str(kv),
                    )
                    for kv in opt_list
                ],
                mode=SelectSelectorMode.DROPDOWN,
                custom_value=custom_value,
                multiple=True if multi_select else False,
            )
        )


CLOUD_CONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REGION, default="eu"): col_to_select(TUYA_ENDPOINTS),
        vol.Optional(CONF_CLIENT_ID): cv.string,
        vol.Optional(CONF_CLIENT_SECRET): cv.string,
        vol.Optional(CONF_USER_ID): cv.string,
        vol.Optional(CONF_USERNAME, default=DOMAIN): cv.string,
        vol.Required(CONF_NO_CLOUD, default=False): bool,
        vol.Optional(CONF_MAC_RETRIEVAL, default=False): bool,
        vol.Optional(CONF_DOWNLOAD_CLOUD_INFO, default=False): bool,
    }
)

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FRIENDLY_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_LOCAL_KEY): cv.string,
        vol.Required(CONF_PROTOCOL_VERSION, default="auto"): col_to_select(
            ["auto"] + sorted(SUPPORTED_PROTOCOL_VERSIONS)
        ),
        vol.Required(CONF_ENABLE_DEBUG, default=False): bool,
        vol.Optional(CONF_SCAN_INTERVAL): int,
        vol.Optional(CONF_MANUAL_DPS): cv.string,
        vol.Optional(CONF_RESET_DPIDS): str,
        vol.Optional(CONF_DEVICE_SLEEP_TIME): int,
        vol.Optional(CONF_NODE_ID, default=None): vol.Any(None, cv.string),
        # Read-only info fields
        vol.Optional("local_ip"): cv.string,
        vol.Optional("cloud_ip"): cv.string,
        vol.Optional("mac"): cv.string,
        vol.Optional("cloud_mac"): cv.string,
        vol.Optional("cloud_product_name"): cv.string,
        vol.Optional("cloud_category"): cv.string,
        vol.Optional("cloud_model"): cv.string,
        vol.Optional("cloud_uuid"): cv.string,
        vol.Optional("cloud_online"): cv.string,
        vol.Optional("cloud_category"): cv.string,
        vol.Optional("cloud_product_id"): cv.string,
        vol.Optional("cloud_product_name"): cv.string,
        vol.Optional("cloud_status"): cv.string,
        vol.Optional("cloud_model"): cv.string,
        vol.Optional("cloud_uuid"): cv.string,
        vol.Optional("cloud_online"): cv.string,
        vol.Optional("cloud_category"): cv.string,
        vol.Optional("cloud_product_id"): cv.string,
        vol.Optional("cloud_product_name"): cv.string,
        vol.Optional("cloud_status"): cv.string,
        vol.Optional("cloud_model"): cv.string,
        vol.Optional("cloud_uuid"): cv.string,
        vol.Optional("cloud_online"): cv.string,
        vol.Optional("cloud_category"): cv.string,
        vol.Optional("cloud_product_id"): cv.string,
        vol.Optional("cloud_product_name"): cv.string,
        vol.Optional("cloud_status"): cv.string,
        vol.Optional("cloud_model"): cv.string,
        vol.Optional("cloud_uuid"): cv.string,
        vol.Optional("cloud_online"): cv.string,
        vol.Optional("cloud_category"): cv.string,
        vol.Optional("cloud_product_id"): cv.string,
        vol.Optional("cloud_product_name"): cv.string,
        vol.Optional("cloud_status"): cv.string,
    }
)

PICK_ENTITY_SCHEMA = vol.Schema(
    {vol.Required(PLATFORM_TO_ADD, default="switch"): col_to_select(PLATFORMS)}
)


CONF_MASS_CONFIGURE = "mass_configure"
MASS_CONFIGURE_SCHEMA = {vol.Optional(CONF_MASS_CONFIGURE, default=False): bool}
CUSTOM_DEVICE = {"Add Device Manually": "..."}


class LocaltuyaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LocalTuya integration."""

    VERSION = ENTRIES_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow for this handler."""
        return LocalTuyaOptionsFlowHandler(config_entry)
    async def async_step_connecting(self, user_input=None):
        """Step to show connection progress."""
        if not hasattr(self, "_validate_task"):
             return await self.async_step_configure_device()

        if not self._validate_task.done():
            return self.async_show_progress(
                step_id="connecting",
                progress_action="connecting",
                progress_task=self._validate_task
            )

        # Task is done, get result
        try:
            valid_data = self._validate_task.result()
            self.dps_strings = valid_data[CONF_DPS_STRINGS]
            self.device_data[CONF_PROTOCOL_VERSION] = valid_data[CONF_PROTOCOL_VERSION]
            
            # Clear task
            if hasattr(self, "_validate_task"):
                delattr(self, "_validate_task")

            return self.async_show_progress_done(next_step_id="device_setup_method")

        except Exception as ex:
            _LOGGER.debug(f"[TUYA-DEBUG] Validation task failed: {ex}")
            if hasattr(self, "_validate_task"):
                delattr(self, "_validate_task")
            return self.async_show_form(
                step_id="configure_device",
                data_schema=DEVICE_SCHEMA,
                errors={"base": "cannot_connect"}
            )

    async def async_step_device_setup_method(self, user_input=None):
        """Manage basic options."""
        DEVICE_SETUP_METHOD = [
            "auto_configure_device",
            "pick_entity_type",
            "choose_template",
        ]
        return self.async_show_menu(
            step_id="device_setup_method",
            menu_options=DEVICE_SETUP_METHOD,
        )

    async def async_step_auto_configure_device(self, user_input=None):
        """Handle asking which templates to use"""
        if not hasattr(self, "_auto_config_task"):
            self._auto_config_task = self.hass.async_create_task(self._async_auto_configure_logic())
        
        if not self._auto_config_task.done():
            return self.async_show_progress(
                step_id="auto_configure_device",
                progress_action="auto_configure_progress",
                progress_task=self._auto_config_task
            )
        
        try:
            res = self._auto_config_task.result()
            if hasattr(self, "_auto_config_task"):
                delattr(self, "_auto_config_task")
            return res
        except Exception as e:
            _LOGGER.warning(f"Auto-discovery task failed: {e}")
            if hasattr(self, "_auto_config_task"):
                delattr(self, "_auto_config_task")
            return self.async_abort(reason="unknown")

    async def _async_auto_configure_logic(self):
        """Logic for auto configuration moved to task."""
        dev_id = self.selected_device
        category = None
        device_data = self.cloud_data.device_list.get(dev_id)
        if device_data:
            category = self.cloud_data.device_list[dev_id].get('category', '')
        # Cloud-first: fetch cloud functions and force all cloud DP IDs into dps_strings
        # so downstream UI/entity generation can see every DP even if local discovery is incomplete.
        cloud_funcs: dict[str, Any] = {}
        try:
            cloud_funcs = await self.cloud_data.async_get_device_functions(dev_id)
        except Exception as ex:
            _LOGGER.warning("[AUTO-CONFIG] Failed to fetch cloud functions for %s: %s", dev_id, ex)
            cloud_funcs = {}

        if cloud_funcs:
            cloud_dp_ids = sorted({str(k) for k in cloud_funcs.keys()}, key=lambda x: int(x) if str(x).isdigit() else 9999)
            # dps_strings are strings like: "1 (value: ?)" or "1 ( code: switch_1 , value: ... )"
            existing_dp_ids = {str(s).split(" ")[0] for s in (self.dps_strings or [])}
            forced = 0
            for dp_id in cloud_dp_ids:
                if dp_id.isdigit() and dp_id not in existing_dp_ids:
                    self.dps_strings.append(f"{dp_id} ( code: {cloud_funcs.get(dp_id, {}).get('code', 'cloud')} , cloud pull )")
                    forced += 1
            if forced:
                self.dps_strings = sorted(self.dps_strings, key=lambda i: int(i.split(" ")[0]))
            _LOGGER.error(
                "[AUTO-CONFIG] Cloud DP force: fetched=%s forced_added=%s total_dps_strings=%s",
                len(cloud_funcs),
                forced,
                len(self.dps_strings or []),
            )
        _LOGGER.error(
            "[AUTO-CONFIG] Device %s cloud category=%s product=%s",
            dev_id,
            category,
            (device_data or {}).get('product_name') or (device_data or {}).get('product_id') or '-',
        )
        
        try:
            if self.device_data is None:
                self.device_data = {}

            localtuya_data = {
                'device_cloud_data': device_data,
                'dps_strings': self.dps_strings,
                'friendly_name': self.device_data.get('friendly_name', 'Garage'),
            }
            # This is the long operation
            dev_data = gen_localtuya_entities(localtuya_data, category)

            if cloud_funcs:
                dev_data, forced_entities = _merge_cloud_entities(dev_data, cloud_funcs)

                if forced_entities:
                    _LOGGER.error(
                        "[AUTO-CONFIG] Forced %s generic entities from cloud DP list (now total=%s)",
                        forced_entities,
                        len(dev_data),
                    )
            
            if dev_id == 'bf27acf38b97deb8d9ogjj':
                dev_data = [
                    {'friendly_name': 'Garage Door', 'id': 1, 'platform': 'cover', 'device_class': 'garage', 'commands_set': 'open_close_stop', 'positioning_mode': 'none', 'current_position_dp': 3, 'position_inverted': True},
                    {'friendly_name': 'Garage Contact', 'id': 3, 'platform': 'binary_sensor', 'device_class': 'garage_door'}
                ]
            if dev_data:
                _LOGGER.error(
                    "[AUTO-CONFIG] Generated %s entities for %s (category=%s)",
                    len(dev_data),
                    dev_id,
                    category,
                )
                self.entities = dev_data
                return await self.async_step_pick_entity_type({'no_additional_entities': True})
            else:
                _LOGGER.error(
                    "[AUTO-CONFIG] No entities generated for %s (category=%s). dps_strings_count=%s",
                    dev_id,
                    category,
                    len(self.dps_strings or []),
                )
                return self.async_abort(reason="no_entities")
        except Exception as e:
            _LOGGER.warning(f"Auto-discovery logic error: {e}")
            raise e

    def __init__(self):
        _LOGGER.error("[TRACER] LocaltuyaConfigFlow instantiated")
        """Initialize a new LocaltuyaConfigFlow."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        _LOGGER.debug("async_step_user called")
        _LOGGER.debug(f"Current language: {self.hass.config.language}")
        errors = {}
        placeholders = {}
        if user_input is not None:
            if user_input.get(CONF_NO_CLOUD):
                for i in [CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_USER_ID]:
                    user_input[i] = ""
                return await self._create_entry(user_input)

            cloud_api, res = await attempt_cloud_connection(user_input)

            if not res:
                return await self._create_entry(user_input)
            errors["base"] = res["reason"]
            # 1004 = Secret, 1106 = USER ID, 2009 = Client ID
            if "1106" in res["msg"]:
                res["msg"] = f"{res['msg']} Check UserID or country code!"
            if "1004" in res["msg"]:
                res["msg"] = f"{res['msg']} Check Secret Key!"
            placeholders = {"msg": res["msg"]}

        defaults = {}
        defaults.update(user_input or {})

        return self.async_show_form(
            step_id="user",
            data_schema=schema_suggested_values(CLOUD_CONFIGURE_SCHEMA, **defaults),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def _create_entry(self, user_input):
        """Register new entry."""
        # if self._async_current_entries():
        #     return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(user_input.get(CONF_USER_ID))
        self._abort_if_unique_id_configured()

        user_input[CONF_DEVICES] = {}

        return self.async_create_entry(
            title=user_input.get(CONF_USERNAME),
            data=user_input,
        )

    async def async_step_import(self, user_input):
        """Handle import from YAML."""
        _LOGGER.error(
            "Configuration via YAML file is no longer supported by this integration."
        )


class LocalTuyaOptionsFlowHandler(OptionsFlow):
    """Handle options flow for LocalTuya integration."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize localtuya options flow."""
        self._entry_id = config_entry.entry_id

        self.selected_device = None
        self.nodeID = None

        self.editing_device: bool = False
        self.device_data: dict = None
        self.dps_strings = []
        self.selected_platform = None
        self.discovered_devices = {}
        self.entities = []
        self.use_template = False
        self.template_device = None

        self._mass_configure_task: asyncio.Task | None = None
        self._mass_configure_result: tuple[dict, dict] | None = None
        self._mass_configure_progress: dict[str, Any] = {
            "current": 0,
            "total": 0,
            "status": "Preparazione configurazione automatica...",
        }

    @property
    def localtuya_data(self) -> HassLocalTuyaData:
        return self.hass.data[DOMAIN][self._entry_id]
    async def async_step_connecting(self, user_input=None):
        """Step to show connection progress."""
        if not hasattr(self, "_validate_task"):
             return await self.async_step_configure_device()

        if not self._validate_task.done():
            return self.async_show_progress(
                step_id="connecting",
                progress_action="connecting",
                progress_task=self._validate_task
            )

        # Task is done, get result
        try:
            valid_data = self._validate_task.result()
            self.dps_strings = valid_data[CONF_DPS_STRINGS]
            self.device_data[CONF_PROTOCOL_VERSION] = valid_data[CONF_PROTOCOL_VERSION]
            
            # Clear task
            if hasattr(self, "_validate_task"):
                delattr(self, "_validate_task")

            return self.async_show_progress_done(next_step_id="device_setup_method")

        except Exception as ex:
            _LOGGER.debug(f"[TUYA-DEBUG] Validation task failed: {ex}")
            if hasattr(self, "_validate_task"):
                delattr(self, "_validate_task")
            return self.async_show_form(
                step_id="configure_device",
                data_schema=DEVICE_SCHEMA,
                errors={"base": "cannot_connect"}
            )

    async def async_step_device_setup_method(self, user_input=None):
        """Manage basic options."""
        DEVICE_SETUP_METHOD = [
            "auto_configure_device",
            "pick_entity_type",
            "choose_template",
        ]
        return self.async_show_menu(
            step_id="device_setup_method",
            menu_options=DEVICE_SETUP_METHOD,
        )

    async def async_step_auto_configure_device(self, user_input=None):
        """Handle asking which templates to use"""
        if not hasattr(self, "_auto_config_task"):
            self._auto_config_task = self.hass.async_create_task(self._async_auto_configure_logic())
        
        if not self._auto_config_task.done():
            return self.async_show_progress(
                step_id="auto_configure_device",
                progress_action="auto_configure_progress",
                progress_task=self._auto_config_task
            )
        
        try:
            res = self._auto_config_task.result()
            if hasattr(self, "_auto_config_task"):
                delattr(self, "_auto_config_task")
            return res
        except Exception as e:
            _LOGGER.warning(f"Auto-discovery task failed: {e}")
            if hasattr(self, "_auto_config_task"):
                delattr(self, "_auto_config_task")
            return self.async_abort(reason="unknown")

    async def _async_auto_configure_logic(self):
        """Logic for auto configuration moved to task."""
        dev_id = self.selected_device
        category = None
        device_data = self.cloud_data.device_list.get(dev_id)
        if device_data:
            category = self.cloud_data.device_list[dev_id].get('category', '')

        # Cloud-first: fetch cloud functions and force all cloud DP IDs into dps_strings
        # so downstream UI/entity generation can see every DP even if local discovery is incomplete.
        cloud_funcs: dict[str, Any] = {}
        try:
            cloud_funcs = await self.cloud_data.async_get_device_functions(dev_id)
        except Exception as ex:
            _LOGGER.warning("[AUTO-CONFIG] Failed to fetch cloud functions for %s: %s", dev_id, ex)
            cloud_funcs = {}

        if cloud_funcs:
            cloud_dp_ids = sorted({str(k) for k in cloud_funcs.keys()}, key=lambda x: int(x) if str(x).isdigit() else 9999)
            existing_dp_ids = {str(s).split(" ")[0] for s in (self.dps_strings or [])}
            forced = 0
            for dp_id in cloud_dp_ids:
                if dp_id.isdigit() and dp_id not in existing_dp_ids:
                    self.dps_strings.append(
                        f"{dp_id} ( code: {cloud_funcs.get(dp_id, {}).get('code', 'cloud')} , cloud pull )"
                    )
                    forced += 1
            if forced:
                self.dps_strings = sorted(self.dps_strings, key=lambda i: int(i.split(" ")[0]))
            _LOGGER.error(
                "[AUTO-CONFIG] Cloud DP force: fetched=%s forced_added=%s total_dps_strings=%s",
                len(cloud_funcs),
                forced,
                len(self.dps_strings or []),
            )
        
        try:
            if self.device_data is None:
                self.device_data = {}

            localtuya_data = {
                'device_cloud_data': device_data,
                'dps_strings': self.dps_strings,
                'friendly_name': self.device_data.get('friendly_name', 'Garage'),
            }
            # This is the long operation
            dev_data = gen_localtuya_entities(localtuya_data, category)

            if cloud_funcs:
                dev_data, forced_entities = _merge_cloud_entities(dev_data, cloud_funcs)

                if forced_entities:
                    _LOGGER.error(
                        "[AUTO-CONFIG] Forced %s generic entities from cloud DP list (now total=%s)",
                        forced_entities,
                        len(dev_data),
                    )
            
            if dev_id == 'bf27acf38b97deb8d9ogjj':
                dev_data = [
                    {'friendly_name': 'Garage Door', 'id': 1, 'platform': 'cover', 'device_class': 'garage', 'commands_set': 'open_close_stop', 'positioning_mode': 'none', 'current_position_dp': 3, 'position_inverted': True},
                    {'friendly_name': 'Garage Contact', 'id': 3, 'platform': 'binary_sensor', 'device_class': 'garage_door'}
                ]
            if dev_data:
                self.entities = dev_data
                return await self.async_step_pick_entity_type({'no_additional_entities': True})
            else:
                return self.async_abort(reason="no_entities")
        except Exception as e:
            _LOGGER.warning(f"Auto-discovery logic error: {e}")
            raise e

    @property
    def cloud_data(self) -> TuyaCloudApi:
        return self.localtuya_data.cloud_data

    async def async_step_init(self, user_input=None):
        _LOGGER.debug("async_step_init called")
        """Manage basic options."""
        configure_menu = CONFIGURE_MENU.copy()
        # Remove Reconfigure existing device option if there is no existed devices.
        if not self.config_entry.data[CONF_DEVICES]:
            configure_menu.pop(configure_menu.index(CONF_EDIT_DEVICE))

        if not self.config_entry.data.get(CONF_NO_CLOUD, True):
            self.hass.async_create_task(self.cloud_data.async_get_devices_list())

        return self.async_show_menu(step_id="init", menu_options=configure_menu)

    async def async_step_configure_cloud(self, user_input=None):
        _LOGGER.debug("async_step_configure_cloud called")
        """Handle the initial step."""
        errors = {}
        placeholders = {}
        if user_input is not None:
            username = user_input.get(CONF_USERNAME)
            if user_input.get(CONF_NO_CLOUD):
                new_data = self.config_entry.data.copy()
                new_data.update(user_input)
                for i in [CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_USER_ID]:
                    new_data[i] = ""

                return self._update_entry(new_data, new_title=username)

            cloud_api, res = await attempt_cloud_connection(user_input)

            if not res:
                new_data = self.config_entry.data.copy()
                new_data.update(user_input)
                # Save mac_retrieval setting at config entry level
                if CONF_MAC_RETRIEVAL in user_input:
                    new_data[CONF_MAC_RETRIEVAL] = user_input[CONF_MAC_RETRIEVAL]
                # Save download_cloud_info setting
                if CONF_DOWNLOAD_CLOUD_INFO in user_input:
                    new_data[CONF_DOWNLOAD_CLOUD_INFO] = user_input[CONF_DOWNLOAD_CLOUD_INFO]
                cloud_devs = cloud_api.device_list
                for dev_id, dev in new_data[CONF_DEVICES].items():
                    if CONF_MODEL not in dev and dev_id in cloud_devs:
                        model = cloud_devs[dev_id].get(CONF_PRODUCT_NAME)
                        new_data[CONF_DEVICES][dev_id][CONF_MODEL] = model

                # Update entry first, then trigger MAC/cloud info retrieval if enabled
                self._update_entry(new_data, new_title=username)
                
                # Trigger MAC retrieval for all devices if enabled
                if new_data.get(CONF_MAC_RETRIEVAL, False):
                    await self._trigger_mac_retrieval(cloud_api, new_data)
                
                # Download all cloud info for all devices if enabled
                if new_data.get(CONF_DOWNLOAD_CLOUD_INFO, False):
                    await self._download_all_cloud_info(cloud_api, new_data)

                return self.async_create_entry(title="", data={})

            errors["base"] = res["reason"]
            placeholders = {"msg": res["msg"]}

        defaults = self.config_entry.data.copy()
        defaults.update(user_input or {})
        defaults[CONF_NO_CLOUD] = False

        return self.async_show_form(
            step_id="configure_cloud",
            data_schema=schema_suggested_values(CLOUD_CONFIGURE_SCHEMA, **defaults),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def _trigger_mac_retrieval(self, cloud_api, entry_data):
        """Trigger MAC retrieval for all devices without MAC."""
        if not entry_data.get(CONF_MAC_RETRIEVAL, False):
            return

        devices = entry_data.get(CONF_DEVICES, {})
        devices_without_mac = [
            dev_id for dev_id, dev_config in devices.items()
            if not dev_config.get(CONF_MAC)
        ]

        if not devices_without_mac:
            return

        try:
            # Call factory info API for all devices at once
            device_ids = ",".join(devices_without_mac)
            factory_info = await cloud_api.async_get_device_factory_info(device_ids)
            
            if factory_info and "result" in factory_info and factory_info["result"]:
                new_data = entry_data.copy()
                updated = False
                for device_info in factory_info["result"]:
                    dev_id = device_info.get("id") or device_info.get("device_id")
                    mac = device_info.get("mac")
                    if dev_id and mac and mac != "00:00:00:00:00:00" and dev_id in new_data[CONF_DEVICES]:
                        new_data[CONF_DEVICES][dev_id][CONF_MAC] = mac
                        updated = True
                        _LOGGER.info(f"MAC address retrieved for {dev_id}: {mac}")
                
                if updated:
                    new_data[ATTR_UPDATED_AT] = str(int(time.time() * 1000))
                    self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
        except Exception as e:
            _LOGGER.warning(f"Failed to retrieve MAC addresses: {e}")

    async def _download_all_cloud_info(self, cloud_api, entry_data):
        """Download all cloud info (MAC, IP, product name, etc.) for all devices."""
        devices = entry_data.get(CONF_DEVICES, {})
        if not devices:
            return

        try:
            # Get all device IDs
            device_ids = list(devices.keys())
            _LOGGER.info(f"Downloading cloud info for {len(device_ids)} devices...")

            # Get factory info (MAC) for all devices
            device_ids_str = ",".join(device_ids)
            factory_info = await cloud_api.async_get_device_factory_info(device_ids_str)
            
            # Get full device list from cloud for IP, product name, model, etc.
            await cloud_api.async_get_devices_list(force_update=True)
            cloud_devices = cloud_api.device_list

            new_data = entry_data.copy()
            updated = False

            # Update from factory info (MAC)
            if factory_info and "result" in factory_info and factory_info["result"]:
                for device_info in factory_info["result"]:
                    dev_id = device_info.get("id") or device_info.get("device_id")
                    mac = device_info.get("mac")
                    sn = device_info.get("sn")
                    uuid = device_info.get("uuid")
                    if dev_id and mac and mac != "00:00:00:00:00:00" and dev_id in new_data[CONF_DEVICES]:
                        new_data[CONF_DEVICES][dev_id][CONF_MAC] = mac
                        if sn:
                            new_data[CONF_DEVICES][dev_id]["cloud_sn"] = sn
                        if uuid:
                            new_data[CONF_DEVICES][dev_id]["cloud_uuid"] = uuid
                        updated = True
                        _LOGGER.info(f"MAC address retrieved for {dev_id}: {mac}")

            # Update from cloud device list (IP, product name, model, category, online status)
            for dev_id, cloud_dev in cloud_devices.items():
                if dev_id in new_data[CONF_DEVICES]:
                    dev_data = new_data[CONF_DEVICES][dev_id]
                    if cloud_dev.get("ip"):
                        dev_data["cloud_ip"] = cloud_dev["ip"]
                        updated = True
                    if cloud_dev.get("product_name"):
                        dev_data["cloud_product_name"] = cloud_dev["product_name"]
                        updated = True
                    if cloud_dev.get("model"):
                        dev_data["cloud_model"] = cloud_dev["model"]
                        updated = True
                    if cloud_dev.get("category"):
                        dev_data["cloud_category"] = cloud_dev["category"]
                        updated = True
                    if cloud_dev.get("online") is not None:
                        dev_data["cloud_online"] = cloud_dev["online"]
                        updated = True
                    if cloud_dev.get("product_id"):
                        dev_data["cloud_product_id"] = cloud_dev["product_id"]
                        updated = True
                    if cloud_dev.get("status"):
                        dev_data["cloud_status"] = cloud_dev["status"]
                        updated = True

            if updated:
                new_data[ATTR_UPDATED_AT] = str(int(time.time() * 1000))
                self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
                _LOGGER.info(f"Cloud info downloaded and updated for {len(devices)} devices")
            else:
                _LOGGER.warning("No cloud info updates were applied")
        except Exception as e:
            _LOGGER.warning(f"Failed to download all cloud info: {e}")

    async def async_step_manage_network(self, user_input=None):
        """Manage network blocking for Tuya devices."""
        status = "Pronto"
        
        # Check cloud connection status
        cloud_configured = False
        if self.config_entry.data.get(CONF_CLIENT_ID) and self.config_entry.data.get(CONF_CLIENT_SECRET) and self.config_entry.data.get(CONF_USER_ID):
            cloud_configured = True
        
        cloud_status = "☁️ Cloud configurato e connesso" if cloud_configured else "☁️ Cloud NON configurato"
        
        # Set default action: block if cloud configured, unblock if not
        default_action = "block" if cloud_configured else "unblock"
        
        if user_input is not None:
            action = user_input.get("action")
            devices = self.config_entry.data.get(CONF_DEVICES, {})
            ips = [dev.get(CONF_HOST) for dev in devices.values() if dev.get(CONF_HOST)]

            if not ips:
                status = "Nessun dispositivo configurato."
            else:
                # Ensure table, set and chain exist
                await self._run_router_command("nft add table inet tuya_block")
                await self._run_router_command(
                    "nft add set inet tuya_block blocked_ips '{ type ipv4_addr ; }'"
                )
                await self._run_router_command(
                    "nft add chain inet tuya_block forward '{ type filter hook forward priority -10 ; policy accept ; }'"
                )
                await self._run_router_command(
                    "nft add rule inet tuya_block forward ip saddr @blocked_ips drop"
                )
                await self._run_router_command(
                    "nft add rule inet tuya_block forward ip daddr @blocked_ips drop"
                )

                if action == "block":
                    # Clear and re-add to avoid "element already exists" errors
                    await self._run_router_command("nft flush set inet tuya_block blocked_ips")
                    for ip in ips:
                        await self._run_router_command(
                            f"nft add element inet tuya_block blocked_ips '{{ {ip} }}'"
                        )
                    status = f"Bloccati {len(ips)} dispositivi"
                else:
                    await self._run_router_command("nft flush set inet tuya_block blocked_ips")
                    status = "Tutti i dispositivi sbloccati"

        return self.async_show_form(
            step_id="manage_network",
            data_schema=vol.Schema(
                {
                    vol.Required("action", default=default_action): vol.In(
                        {
                            "block": "Blocca Accesso Internet",
                            "unblock": "Sblocca Accesso Internet",
                        }
                    )
                }
            ),
            description_placeholders={
                "status": status,
                "cloud_status": cloud_status
            },
        )

    async def _run_router_command(self, command):
        """Run a command on the router via SSH."""
        try:
            import subprocess
            ssh_cmd = [
                "ssh",
                "-i", "/config/.ssh/router_key",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "root@192.168.0.11",
                command
            ]
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False, result.stderr
            return True, result.stdout
        except Exception as e:
            return False, str(e)

    async def async_step_add_device(self, user_input=None):
        _LOGGER.debug("async_step_add_device called")
        """Handle adding a new device."""
        # Use cache if available or fallback to manual discovery
        self.editing_device = False
        self.selected_device = None
        errors = {}
        if user_input is not None:
            if user_input[SELECTED_DEVICE] != CUSTOM_DEVICE["Add Device Manually"]:
                self.selected_device = user_input[SELECTED_DEVICE]

            if user_input.pop(CONF_MASS_CONFIGURE, False):
                await self.cloud_data.async_get_devices_dps_query()
                self._mass_configure_progress = {
                    "current": 0,
                    "total": 0,
                    "status": "Preparazione configurazione automatica...",
                }
                self._mass_configure_result = None
                self._mass_configure_task = self.hass.async_create_task(
                    setup_localtuya_devices(
                        self.hass,
                        self.localtuya_data,
                        self.discovered_devices,
                        self.cloud_data.device_list,
                        log_fails=True,
                        progress_callback=self._update_mass_configure_progress,
                    )
                )
                return await self.async_step_mass_configure_progress()

            return await self.async_step_configure_device()

        self.discovered_devices = {}
        data = self.hass.data.get(DOMAIN)

        if data and DATA_DISCOVERY in data:
            self.discovered_devices = data[DATA_DISCOVERY].devices
        else:
            self.discovered_devices, errors = await discover_devices()

        # Ensure cloud device list is loaded before building the dropdown
        cloud_load_error = None
        cloud_debug_info = {}
        _LOGGER.debug("async_step_add_device: cloud device list has %d entries, no_cloud=%s",
                      len(self.cloud_data.device_list),
                      self.config_entry.data.get(CONF_NO_CLOUD, True))
        if not self.cloud_data.device_list and not self.config_entry.data.get(CONF_NO_CLOUD, True):
            _LOGGER.debug("async_step_add_device: loading cloud device list...")
            result = await self.cloud_data.async_get_devices_list()
            _LOGGER.debug("async_step_add_device: cloud device list load result: %s, now has %d entries",
                          result, len(self.cloud_data.device_list))
            if result and result != "ok":
                # Extract debug info from cloud API if available
                if isinstance(result, dict) and result.get("_debug"):
                    cloud_debug_info = result["_debug"]
                cloud_load_error = f"Cloud API error: {result}"
        
        _LOGGER.debug("async_step_add_device: device_list keys count=%d, sample keys: %s",
                      len(self.cloud_data.device_list),
                      list(self.cloud_data.device_list.keys())[:3])

        # If cloud load failed, ask user to provide device list JSON manually
        if cloud_load_error:
            return await self.async_step_add_device_manual_cloud()

        allDevices = mergeDevicesList(
            self.discovered_devices, self.cloud_data.device_list
        )

        self.discovered_devices = allDevices
        devices = {}
        # To avoid duplicated entities we will get all devices in every hub.
        entries = self.hass.config_entries.async_entries(DOMAIN)
        configured_Devices = []
        for entry in entries:
            for devID in entry.data[CONF_DEVICES].keys():
                configured_Devices.append(devID)

        for dev_id, dev in allDevices.items():
            if dev_id not in configured_Devices:
                if dev.get(CONF_NODE_ID, None) is not None:
                    devices[dev_id] = "Sub Device"
                else:
                    # Pass the name from cloud data if available
                    cloud_name = None
                    if dev_id in self.cloud_data.device_list:
                        cloud_name = self.cloud_data.device_list[dev_id].get(CONF_NAME)
                    devices[dev_id] = {
                        CONF_TUYA_IP: dev.get(CONF_TUYA_IP, ""),
                        "name": cloud_name or dev_id,
                    }

        # Add cloud error to form errors if present
        if cloud_load_error:
            errors["base"] = cloud_load_error
            # Add debug info to description placeholders
            if cloud_debug_info:
                errors["_debug_payload"] = str(cloud_debug_info)

        return self.async_show_form(
            step_id="add_device",
            data_schema=devices_schema(devices, self.cloud_data.device_list),
            errors=errors,
            description_placeholders={"debug_payload": str(cloud_debug_info)} if cloud_debug_info else {},
        )

    async def async_step_add_device_manual_cloud(self, user_input=None):
        """Handle manual cloud device list JSON input when cloud API fails."""
        _LOGGER.debug("async_step_add_device_manual_cloud called, user_input=%s",
                      user_input is not None)
        errors = {}

        # Cache file path for the manual cloud device list JSON
        cache_path = Path(self.hass.config.config_dir) / ".tuya_cloud_manual_list_cache.json"

        # Check for existing cache
        cached_json = None
        if cache_path.exists():
            try:
                cached_json = json.loads(cache_path.read_text())
                _LOGGER.debug("Loaded existing cache from %s", cache_path)
            except Exception as ex:
                _LOGGER.warning("Failed to load cache from %s: %s", cache_path, ex)
                cached_json = None
        else:
            _LOGGER.debug("No cache file found at %s", cache_path)

        if user_input is not None:
            # User chose option from selector
            action = user_input.get("action")
            json_input = user_input.get("cloud_device_json", "")
            _LOGGER.info("user_input received: action=%s, has_json=%s", action, bool(json_input and json_input.strip()))

            if action == "update_cache":
                _LOGGER.info("Branch: update_cache, fetching fresh device list from Tuya Cloud...")
                try:
                    fresh_result = await self.cloud_data.async_get_devices_list(force_update=True)
                    if fresh_result == "ok":
                        _LOGGER.info("Branch: update_cache fetched fresh cloud device list OK (%d devices)",
                                       len(self.cloud_data.device_list))
                        # Compute configured device IDs to filter them out
                        configured_devices = set()
                        for entry in self.hass.config_entries.async_entries(DOMAIN):
                            for dev_id in entry.data.get(CONF_DEVICES, {}).keys():
                                configured_devices.add(dev_id)
                        devices_list = [
                            {"res_id": dev_id, "res_type": 0}
                            for dev_id in self.cloud_data.device_list
                            if dev_id not in configured_devices
                        ]
                        if not devices_list:
                            _LOGGER.info("Branch: update_cache all devices already configured")
                            errors["base"] = "all_devices_configured"
                            parsed = None
                        else:
                            parsed = {"result": {"data": devices_list}}
                            # Save fresh data to cache
                            try:
                                cache_path.write_text(json.dumps(parsed))
                                _LOGGER.info("Branch: update_cache cache updated with fresh data (%d devices)",
                                               len(devices_list))
                            except Exception as ex:
                                _LOGGER.warning("Branch: update_cache failed to write cache: %s", ex)
                    else:
                        _LOGGER.warning("Branch: update_cache failed to fetch data: %s", fresh_result)
                        errors["base"] = "json_required"
                        parsed = None
                except Exception as ex:
                    _LOGGER.exception("Branch: update_cache fetch failed")
                    errors["base"] = str(ex)
                    parsed = None
            elif action == "use_cached" and cached_json is not None:
                _LOGGER.info("Branch: using cached JSON")
                parsed = cached_json
            elif action == "paste_json":
                json_input = json_input.strip()
                _LOGGER.info("Branch: paste_json, json_input length=%d", len(json_input))
                if not json_input:
                    _LOGGER.info("Branch: paste_json but json_input is empty")
                    errors["base"] = "json_required"
                    parsed = None
                else:
                    try:
                        parsed = json.loads(json_input)
                        _LOGGER.info("Branch: JSON parsed successfully, top-level keys=%s", list(parsed.keys()))
                    except json.JSONDecodeError as ex:
                        _LOGGER.info("Branch: JSON parse failed: %s", ex)
                        errors["base"] = "json_invalid"
                        parsed = None
            elif action == "use_cached" and cached_json is None:
                _LOGGER.info("Branch: use_cached selected but no cache file exists")
                errors["base"] = "json_required"
                parsed = None
            else:
                # action is None or unrecognized: default to paste_json behavior
                _LOGGER.info("Branch: action=%s (unrecognized or None), defaulting to paste_json behavior", action)
                json_input = json_input.strip() if json_input else ""
                if not json_input:
                    _LOGGER.info("Branch: no action and no JSON provided (action=%s)", action)
                    errors["base"] = "json_required"
                    parsed = None
                else:
                    try:
                        parsed = json.loads(json_input)
                        _LOGGER.info("Branch: JSON parsed (default path), top-level keys=%s", list(parsed.keys()))
                    except json.JSONDecodeError as ex:
                        _LOGGER.info("Branch: JSON parse failed (default path): %s", ex)
                        errors["base"] = "json_invalid"
                        parsed = None

            if parsed is not None and not errors:
                _LOGGER.debug("Parsed JSON is valid, checking format...")
                try:
                    if "result" in parsed and isinstance(parsed["result"], dict) and "data" in parsed["result"]:
                        _LOGGER.info("Format 1 detected: result.data structure")
                        # Format 1: Initial device list (res_id based)
                        devices_data = parsed["result"]["data"]
                        if not isinstance(devices_data, list):
                            _LOGGER.debug("Format 1: devices_data is not a list, type=%s", type(devices_data))
                            errors["base"] = "json_invalid_data"
                        else:
                            _LOGGER.debug("Format 1: devices_data has %d entries", len(devices_data))
                            configured_devices = set()
                            configured_macs = set()
                            for entry in self.hass.config_entries.async_entries(DOMAIN):
                                for dev_id, dev_conf in entry.data.get(CONF_DEVICES, {}).items():
                                    configured_devices.add(dev_id)
                                    mac = dev_conf.get("mac") or dev_conf.get("mac_address") or ""
                                    if mac:
                                        configured_macs.add(mac.lower().replace(":", "").replace("-", ""))
                            _LOGGER.info("Configured device IDs: %s; MACs: %s", configured_devices, configured_macs)

                            unconfigured_devices = [
                                d for d in devices_data
                                if (d.get("res_id") or d.get("id"))
                                and (d.get("res_id") or d.get("id")) not in configured_devices
                                and not (
                                    d.get("mac")
                                    and d.get("mac").lower().replace(":", "").replace("-", "") in configured_macs
                                )
                            ]
                            _LOGGER.info("Unconfigured device IDs: %s", [d.get("res_id") or d.get("id") for d in unconfigured_devices])

                            if not unconfigured_devices:
                                _LOGGER.debug("No unconfigured devices, setting error 'all_devices_configured'")
                                errors["base"] = "all_devices_configured"
                            else:
                                # Cache the raw JSON for future use
                                if action == "paste_json":
                                    try:
                                        cache_path.write_text(json_input)
                                        _LOGGER.debug("Cached raw JSON to %s", cache_path)
                                    except Exception as ex:
                                        _LOGGER.warning("Failed to write cache to %s: %s", cache_path, ex)

                                self._manual_device_ids = [
                                    d.get("res_id") or d.get("id") for d in unconfigured_devices
                                ]
                                _LOGGER.info("Set _manual_device_ids=%s", self._manual_device_ids)
                                # Cache the unconfigured device IDs so next step knows which devices to configure
                                try:
                                    (Path(self.hass.config.config_dir) / ".tuya_manual_cloud_ids_cache.json").write_text(
                                        json.dumps(self._manual_device_ids)
                                    )
                                    _LOGGER.debug("Cached unconfigured IDs to .tuya_manual_cloud_ids_cache.json")
                                except Exception as ex:
                                    _LOGGER.warning("Failed to write IDs cache: %s", ex)
                                # Show the unconfigured device list summary then ask for detailed JSON
                                _LOGGER.info("Calling async_step_add_device_manual_cloud_detail()")
                                return await self.async_step_add_device_manual_cloud_detail()

                    elif "result" in parsed and isinstance(parsed["result"], list):
                        _LOGGER.info("Format 2 detected in step 1: result is list (detailed device info)")
                        # Format 2: Detailed device info
                        devices_data = parsed["result"]
                        if not isinstance(devices_data, list):
                            _LOGGER.debug("Format 2: devices_data is not a list, type=%s", type(devices_data))
                            errors["base"] = "json_invalid_data"
                        else:
                            _LOGGER.debug("Format 2: devices_data has %d entries", len(devices_data))
                            manual_device_list = {}
                            manual_ids = getattr(self, '_manual_device_ids', None)
                            for dev in devices_data:
                                dev_id = dev.get("id")
                                if dev_id and (manual_ids is None or dev_id in manual_ids):
                                    _LOGGER.info("Format 2 step1: including dev_id=%s (no manual_ids filter active)", dev_id)
                                    manual_device_list[dev_id] = {
                                        "id": dev_id,
                                        "name": dev.get("name") or dev.get("custom_name") or dev_id,
                                        "local_key": dev.get("local_key") or "",
                                        "ip": dev.get("ip") or "",
                                        "product_id": dev.get("product_id") or "",
                                        "product_name": dev.get("product_name") or "",
                                        "category": dev.get("category") or "",
                                        "online": dev.get("is_online", dev.get("online", True)),
                                        "mac": dev.get("mac") or "",
                                        "uuid": dev.get("uuid") or "",
                                        "version": dev.get("version") or "auto",
                                        "model": dev.get("model") or "",
                                        "active_time": dev.get("active_time"),
                                        "create_time": dev.get("create_time"),
                                        "update_time": dev.get("update_time"),
                                        "bind_space_id": dev.get("bind_space_id"),
                                        "custom_name": dev.get("custom_name") or "",
                                        "icon": dev.get("icon") or "",
                                        "lat": dev.get("lat"),
                                        "lon": dev.get("lon"),
                                        "sub": dev.get("sub", False),
                                        "time_zone": dev.get("time_zone"),
                                    }
                            _LOGGER.info("Format 2 step1: built manual_device_list with %d entries (manual_ids_set=%s)",
                                          len(manual_device_list), manual_ids is not None)

                            # Pre-import check: filter out already-configured devices
                            configured_ids = set()
                            configured_macs = set()
                            for existing_entry in self.hass.config_entries.async_entries(DOMAIN):
                                for existing_dev_id, existing_dev in existing_entry.data.get(
                                    CONF_DEVICES, {}
                                ).items():
                                    configured_ids.add(existing_dev_id)
                                    mac = existing_dev.get("mac") or existing_dev.get("mac_address") or ""
                                    if mac:
                                        configured_macs.add(mac.lower().replace(":", "").replace("-", ""))

                            filtered_manual_device_list = {}
                            for dev_id, dev_data in manual_device_list.items():
                                if dev_id in configured_ids:
                                    _LOGGER.info("Pre-import check (step1): skipping already-configured device %s", dev_id)
                                    continue
                                dev_mac = (dev_data.get("mac") or "").lower().replace(":", "").replace("-", "")
                                if dev_mac and dev_mac in configured_macs:
                                    _LOGGER.info("Pre-import check (step1): skipping device %s with duplicate MAC %s", dev_id, dev_mac)
                                    continue
                                filtered_manual_device_list[dev_id] = dev_data

                            manual_device_list = filtered_manual_device_list
                            _LOGGER.info("Pre-import check (step1): %d/%d devices pass validation, %d filtered out",
                                          len(manual_device_list), len(devices_data),
                                          len(devices_data) - len(manual_device_list))

                            if not manual_device_list:
                                _LOGGER.info("Pre-import check (step1): all devices filtered, nothing to import")
                                errors["base"] = "all_devices_configured"
                            else:
                                self.cloud_data.device_list.update(manual_device_list)
                                _LOGGER.info(f"Manually added {len(manual_device_list)} devices from detailed JSON input (step 1)")

                                if hasattr(self, "_manual_device_ids"):
                                    delattr(self, "_manual_device_ids")

                                return await self.async_step_add_device()

                    else:
                        _LOGGER.debug("Format unrecognized: keys=%s", list(parsed.keys()), exc_info=True)
                        errors["base"] = "json_invalid_format"

                except json.JSONDecodeError:
                    _LOGGER.debug("json.JSONDecodeError during format check")
                    errors["base"] = "json_invalid"
                except Exception as ex:
                    _LOGGER.exception("Error parsing manual cloud JSON")
                    errors["base"] = str(ex)

        # Build form schema
        import voluptuous as vol
        cache_option = cached_json is not None
        if cache_option:
            schema = vol.Schema({
                vol.Required("action", default="paste_json"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value="use_cached", label="📂 Use cached device list"),
                            SelectOptionDict(value="update_cache", label="🔄 Fetch fresh from Tuya Cloud"),
                            SelectOptionDict(value="paste_json", label="📝 Paste new JSON"),
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Optional("cloud_device_json"): str,
            })
        else:
            schema = vol.Schema({
                vol.Required("cloud_device_json"): str,
            })

        return self.async_show_form(
            step_id="add_device_manual_cloud",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "json_format": '''{
  "result": {
    "data": [
      {"res_id": "bfc0abab874dc1a864q5kn", "res_type": 0},
      {"res_id": "bf054a2177fd16678d9yds", "res_type": 0}
    ],
    "last_row_key": 2031162322342079,
    "page_size": 200
  },
  "success": true,
  "t": 1785229260540,
  "tid": "daa2e1a18a6211f19cb812e3d0098c67"
}''',
                "note": (
                    "Incolla il JSON completo dall'API Tuya Cloud (endpoint /v1.0/users/{uid}/devices). "
                    "Il formato deve contenere 'result.data' con oggetti che hanno 'res_id' (device ID). "
                    + ("⚡ Cache trovata: puoi usare quella salvata, aggiornarla dalla nuvola o incollare un nuovo JSON."
                       if cache_option
                       else "Se incolla il JSON, verrà salvato in cache per i prossimi utilizzi.")
                ),
            },
        )

    async def async_step_add_device_manual_cloud_detail(self, user_input=None):
        """Handle detailed device info JSON input for unconfigured devices."""
        _LOGGER.debug("async_step_add_device_manual_cloud_detail called, user_input=%s, _manual_device_ids=%s",
                      user_input is not None, getattr(self, '_manual_device_ids', 'N/A'))
        errors = {}

        if user_input is not None:
            json_input = user_input.get("cloud_device_json", "").strip()
            _LOGGER.debug("user_input received in detail step, json_input length=%d", len(json_input))
            if not json_input:
                _LOGGER.debug("Branch: json_input is empty")
                errors["base"] = "json_required"
            else:
                try:
                    import json
                    parsed = json.loads(json_input)
                    _LOGGER.debug("Branch: JSON parsed successfully, top-level keys=%s", list(parsed.keys()))

                    # Expect Format 2: Detailed device info
                    if "result" in parsed and isinstance(parsed["result"], list):
                        _LOGGER.info("Format 2 detected in detail step: result is list")
                        devices_data = parsed["result"]
                        if not isinstance(devices_data, list):
                            _LOGGER.debug("Format 2: devices_data is not a list, type=%s", type(devices_data))
                            errors["base"] = "json_invalid_data"
                        else:
                            _LOGGER.debug("Format 2: devices_data has %d entries, _manual_device_ids=%s",
                                          len(devices_data), getattr(self, '_manual_device_ids', 'N/A'))
                            manual_device_list = {}
                            for dev in devices_data:
                                dev_id = dev.get("id")
                                _LOGGER.debug("  checking dev_id=%s against _manual_device_ids=%s",
                                              dev_id, getattr(self, '_manual_device_ids', 'N/A'))
                                if dev_id and dev_id in self._manual_device_ids:
                                    _LOGGER.debug("  MATCH: dev_id=%s found in _manual_device_ids", dev_id)
                                    manual_device_list[dev_id] = {
                                        "id": dev_id,
                                        "name": dev.get("name") or dev.get("custom_name") or dev_id,
                                        "local_key": dev.get("local_key") or "",
                                        "ip": dev.get("ip") or "",
                                        "product_id": dev.get("product_id") or "",
                                        "product_name": dev.get("product_name") or "",
                                        "category": dev.get("category") or "",
                                        "online": dev.get("is_online", dev.get("online", True)),
                                        "mac": dev.get("mac") or "",
                                        "uuid": dev.get("uuid") or "",
                                        "version": dev.get("version") or "auto",
                                        "model": dev.get("model") or "",
                                        "active_time": dev.get("active_time"),
                                        "create_time": dev.get("create_time"),
                                        "update_time": dev.get("update_time"),
                                        "bind_space_id": dev.get("bind_space_id"),
                                        "custom_name": dev.get("custom_name") or "",
                                        "icon": dev.get("icon") or "",
                                        "lat": dev.get("lat"),
                                        "lon": dev.get("lon"),
                                        "sub": dev.get("sub", False),
                                        "time_zone": dev.get("time_zone"),
                                    }
                            _LOGGER.debug("Format 2: built manual_device_list with %d matched entries out of %d total",
                                          len(manual_device_list), len(devices_data))

                            # Pre-import check: filter out any device that may have
                            # slipped through (e.g. manually edited JSON with dupes)
                            configured_ids = set()
                            configured_macs = set()
                            for existing_entry in self.hass.config_entries.async_entries(DOMAIN):
                                for existing_dev_id, existing_dev in existing_entry.data.get(
                                    CONF_DEVICES, {}
                                ).items():
                                    configured_ids.add(existing_dev_id)
                                    mac = existing_dev.get("mac") or existing_dev.get("mac_address") or ""
                                    if mac:
                                        configured_macs.add(mac.lower().replace(":", "").replace("-", ""))

                            filtered_manual_device_list = {}
                            for dev_id, dev_data in manual_device_list.items():
                                if dev_id in configured_ids:
                                    _LOGGER.info("Pre-import check: skipping already-configured device %s", dev_id)
                                    continue
                                dev_mac = (dev_data.get("mac") or "").lower().replace(":", "").replace("-", "")
                                if dev_mac and dev_mac in configured_macs:
                                    _LOGGER.info("Pre-import check: skipping device %s with duplicate MAC %s", dev_id, dev_mac)
                                    continue
                                filtered_manual_device_list[dev_id] = dev_data

                            manual_device_list = filtered_manual_device_list
                            _LOGGER.info("Pre-import check: %d/%d devices pass validation, %d filtered out",
                                          len(manual_device_list), len(devices_data),
                                          len(devices_data) - len(manual_device_list))

                            if not manual_device_list:
                                _LOGGER.info("Pre-import check: all devices filtered, nothing to import")
                                errors["base"] = "all_devices_configured"
                            else:
                                self.cloud_data.device_list.update(manual_device_list)
                                _LOGGER.info(f"Manually added {len(manual_device_list)} devices from detailed JSON input")

                                if hasattr(self, "_manual_device_ids"):
                                    _LOGGER.debug("Deleting _manual_device_ids attribute")
                                    delattr(self, "_manual_device_ids")

                                _LOGGER.debug("Calling async_step_add_device()")
                                return await self.async_step_add_device()
                    else:
                        _LOGGER.debug("Format unrecognized in detail step: keys=%s (is result a list? %s)",
                                      list(parsed.keys()), isinstance(parsed.get("result"), list))
                        errors["base"] = "json_invalid_format"

                except json.JSONDecodeError as ex:
                    _LOGGER.debug("json.JSONDecodeError in detail step: %s", ex)
                    errors["base"] = "json_invalid"
                except Exception as ex:
                    _LOGGER.exception("Error parsing manual cloud JSON in detail step")
                    errors["base"] = str(ex)

        # Build the list of unconfigured device IDs for the user
        _LOGGER.debug("Building device_list_str for form display, has _manual_device_ids=%s",
                       hasattr(self, '_manual_device_ids'))
        device_list_str = ", ".join(self._manual_device_ids) if hasattr(self, "_manual_device_ids") else ""
        device_count = len(self._manual_device_ids) if hasattr(self, "_manual_device_ids") else 0
        
        # Schema for the detailed JSON input (Format 2)
        import voluptuous as vol
        schema = vol.Schema({
            vol.Required("cloud_device_json"): str,
        })
        
        return self.async_show_form(
            step_id="add_device_manual_cloud_detail",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "unconfigured_list": device_list_str,
                "unconfigured_count": str(device_count),
                "json_format": '''{
  "result": [
    {
      "active_time": 1741388374,
      "bind_space_id": "150797786",
      "category": "tdq",
      "create_time": 1695142031,
      "custom_name": "",
      "icon": "smart/icon/ay1533257659316XGZOd/1f21cca41812827d145dc1620bf8a835.jpg",
      "id": "bfc0abab874dc1a864q5kn",
      "ip": "109.53.1.80",
      "is_online": false,
      "lat": "0",
      "local_key": "&t-ii)HEj{'W]PSq",
      "lon": "0",
      "model": "",
      "name": "1CH WiFi Switch Module 3",
      "product_id": "1o5lr0wtvu2bziz6",
      "product_name": "1CH WiFi Switch Module CB3S",
      "sub": false,
      "time_zone": "+01:00",
      "update_time": 1741388379,
      "uuid": "a1fe4be9b7581dbc"
    },
    {
      "active_time": 1784999107,
      "bind_space_id": "150797786",
      "category": "tdq",
      "create_time": 1698482845,
      "custom_name": "luci cucina",
      "icon": "smart/icon/bay1624869296421wDFy/004a59b34f6ea7a794a43c403f23e5c8.png",
      "id": "bf054a2177fd16678d9yds",
      "ip": "109.54.80.116",
      "is_online": true,
      "lat": "0",
      "local_key": "!+6&sWj?;n^a}<_|",
      "lon": "0",
      "model": "",
      "name": "PSW-4CH-CBU",
      "product_id": "ebsml1m0sp7nwjal",
      "product_name": "PSW-4CH-CBU",
      "sub": false,
      "time_zone": "+02:00",
      "update_time": 1784999166,
      "uuid": "1ee361bc7945043b"
    }
  ],
  "success": true,
  "t": 1785230238284,
  "tid": "216c929d8a6511f19f9afa101bc7a5bb"
}''',
                "note": "Incolla qui il JSON con i dettagli completi dei dispositivi NON ancora configurati. L'array 'result' deve contenere oggetti con tutti i campi (inclusi 'id', 'local_key', 'name', 'product_name', 'category', 'ip', 'is_online', 'uuid', ecc.). Verranno importati solo i dispositivi nella lista: {device_list}"
            },
        )

    @callback
    def _update_mass_configure_progress(
        self, current: int, total: int, status: str
    ) -> None:
        """Track mass configure progress for flow dialog."""
        self._mass_configure_progress = {
            "current": current,
            "total": total,
            "status": status,
        }

    async def async_step_mass_configure_progress(self, user_input=None):
        """Show progress for automatic multi-device configuration."""
        if not self._mass_configure_task:
            return self.async_abort(reason="unknown")

        if self._mass_configure_task.done():
            self._mass_configure_result = self._mass_configure_task.result()
            return self.async_show_progress_done(next_step_id="mass_configure_result")

        return self.async_show_progress(
            step_id="mass_configure_progress",
            progress_action=self._mass_configure_progress["status"],
            progress_task=self._mass_configure_task,
        )

    async def async_step_mass_configure_result(self, user_input=None):
        """Handle result of automatic multi-device configuration."""
        devices, fails = self._mass_configure_result or ({}, {})
        self._mass_configure_task = None
        self._mass_configure_result = None

        if devices:
            devices_sucessed, devices_fails = "", ""
            for sucess_dev in devices.values():
                devices_sucessed += f"\n{sucess_dev[CONF_FRIENDLY_NAME]}"
            for fail_dev in fails.values():
                devices_fails += f"\n{fail_dev['name']}: {fail_dev['reason']}"

            msg = f"Succeeded devices: ``{len(devices)}``\n ```{devices_sucessed}\n```"
            if fails:
                msg += f" \n Failed devices: ``{len(fails)}``\n ```{devices_fails}\n```"
            msg += "\nClick on submit to add the devices"

            return await self.async_step_confirm(
                msg=msg,
                confirm_callback=lambda: self._update_entry(devices, CONF_DEVICES),
            )

        return await self.async_step_configure_device()

    async def async_step_edit_device(self, user_input=None):
        _LOGGER.debug("async_step_edit_device called, user_input=%s", user_input)
        """Handle editing a device."""
        self.editing_device = True
        # Use cache if available or fallback to manual discovery
        errors = {}
        if user_input is not None:
            self.selected_device = user_input[SELECTED_DEVICE]
            _LOGGER.debug("Selected device for edit: %s", self.selected_device)
            dev_conf = self.config_entry.data[CONF_DEVICES][self.selected_device]
            self.dps_strings = dev_conf.get(CONF_DPS_STRINGS, gen_dps_strings())
            self.entities = dev_conf[CONF_ENTITIES]
            # Ensure discovered_devices is populated for local IP lookup
            if not self.discovered_devices:
                data = self.hass.data.get(DOMAIN)
                if data and DATA_DISCOVERY in data:
                    self.discovered_devices = data[DATA_DISCOVERY].devices
                    _LOGGER.debug("Using cached discovered_devices: %s", list(self.discovered_devices.keys()))
                else:
                    self.discovered_devices, _ = await discover_devices()
                    _LOGGER.debug("Discovered devices via fresh discovery: %s", list(self.discovered_devices.keys()))
            
# Auto-retrieve MAC if enabled and device doesn't have one
            if self.config_entry.data.get(CONF_MAC_RETRIEVAL, False):
                if not dev_conf.get(CONF_MAC):
                    _LOGGER.info("Auto-retrieving MAC for device %s", self.selected_device)
                    try:
                        cloud_api = self.cloud_data
                        factory_info = await cloud_api.async_get_device_factory_info(self.selected_device)
                        mac_retrieved = False
                        if factory_info and factory_info.get("result"):
                            mac = factory_info["result"][0].get("mac")
                            if mac and mac != "00:00:00:00:00:00":
                                new_data = self.config_entry.data.copy()
                                new_data[CONF_DEVICES][self.selected_device][CONF_MAC] = mac
                                new_data[ATTR_UPDATED_AT] = str(int(time.time() * 1000))
                                self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
                                _LOGGER.info("Auto-retrieved MAC address for %s: %s", self.selected_device, mac)
                                # Refresh dev_conf with new MAC
                                dev_conf = new_data[CONF_DEVICES][self.selected_device]
                                mac_retrieved = True
                        
                        if not mac_retrieved:
                            if isinstance(factory_info, dict) and factory_info.get("_debug"):
                                errors["base"] = f"Cloud API error getting MAC: {factory_info.get('msg', 'unknown')}"
                                errors["_debug_payload"] = str(factory_info["_debug"])
                            else:
                                errors["base"] = "Failed to retrieve MAC from cloud (no result)"
                    except Exception as e:
                        _LOGGER.warning("Failed to auto-retrieve MAC for %s: %s", self.selected_device, e)
                        errors["base"] = f"Failed to get MAC: {e}"
            
            return await self.async_step_configure_device()

        # Build devices dict using actual discovery data for correct IP display
        devices = {}
        # First, get the real discovered devices
        discovery_data = self.hass.data.get(DOMAIN)
        if discovery_data and DATA_DISCOVERY in discovery_data:
            real_discovered = discovery_data[DATA_DISCOVERY].devices
        else:
            real_discovered, _ = await discover_devices()
        
        _LOGGER.debug("Real discovered devices: %s", {k: v.get(CONF_TUYA_IP) for k, v in real_discovered.items()})
        
        for dev_id, configured_dev in self.config_entry.data[CONF_DEVICES].items():
            if configured_dev.get(CONF_NODE_ID, None):
                devices[dev_id] = "Sub Device"
            else:
                # Use discovered local IP if available, fallback to stored host
                if dev_id in real_discovered and real_discovered[dev_id].get(CONF_TUYA_IP):
                    display_host = real_discovered[dev_id][CONF_TUYA_IP]
                    _LOGGER.debug("Device %s: using discovered local IP %s", dev_id, display_host)
                else:
                    display_host = configured_dev[CONF_HOST]
                    _LOGGER.debug("Device %s: using stored host %s", dev_id, display_host)
                devices[dev_id] = display_host

        _LOGGER.debug("Final devices dict for edit_device schema: %s", devices)

        return self.async_show_form(
            step_id="edit_device",
            data_schema=devices_schema(
                devices,
                self.cloud_data.device_list,
                False,
                self.config_entry.data[CONF_DEVICES],
            ),
            errors=errors,
        )

    async def async_step_confirm_cloud_dps(self, user_input=None):
        _LOGGER.debug("async_step_confirm_cloud_dps called")
        """Step to confirm adding missing Cloud DPS."""
        if user_input is not None:
            if user_input.get("add_cloud_dps"):
                # Merge missing cloud DPS into dps_strings
                self.dps_strings = sorted(
                    list(set(self.dps_strings + self.cloud_dps_to_add)),
                    key=lambda i: int(i.split(" ")[0]),
                )
            return await self.async_step_device_setup_method()

        return self.async_show_form(
            step_id="confirm_cloud_dps",
            data_schema=vol.Schema({
                vol.Required("add_cloud_dps", default=True): bool,
            }),
            description_placeholders={
                "missing_dps": ", ".join(self.cloud_dps_to_add)
            },
        )

    async def async_step_configure_device(self, user_input=None):
        _LOGGER.debug("async_step_configure_device called")
        """Handle input of basic info."""
        errors = {}
        placeholders = {}
        dev_id = self.selected_device
        cloud_devs = self.cloud_data.device_list
        if user_input is not None:
            try:
                self.device_data = user_input.copy()
                self.selected_device: str = dev_id or user_input.get(CONF_DEVICE_ID)
                self.nodeID: str = self.nodeID or user_input.get(CONF_NODE_ID)
                if dev_id is not None:
                    if dev_id in cloud_devs:
                        self.device_data[CONF_MODEL] = cloud_devs[dev_id].get(
                            CONF_PRODUCT_NAME
                        )
                    # Pulls some of device data that aren't required from user in config_flow.
                    if device := self.discovered_devices.get(dev_id):
                        self.device_data[CONF_PRODUCT_KEY] = device.get("productKey")
                        if gateway_id := device.get(CONF_GATEWAY_ID):
                            self.device_data[CONF_GATEWAY_ID] = gateway_id

# Handle Inputs on edit device mode.
                if self.editing_device:
                    dev_config: dict = self.config_entry.data[CONF_DEVICES].get(
                        dev_id, {}
                    )
                    if self.device_data.pop(EXPORT_CONFIG, False):
                        dev_config = self.config_entry.data[CONF_DEVICES][dev_id].copy()
                        await self.hass.async_add_executor_job(
                            templates.export_config,
                            dev_config,
                            self.device_data[CONF_FRIENDLY_NAME],
                        )
                        return self.async_create_entry(title="", data={})
                    
                    
                    # We will restore device details if it's already existed!
                    for res_conf in [CONF_GATEWAY_ID, CONF_MODEL, CONF_PRODUCT_KEY]:
                        if dev_config.get(res_conf):
                            self.device_data[res_conf] = dev_config.get(res_conf)
                    
                    # Restore cloud info fields from existing device config
                    for res_conf in ["cloud_ip", "cloud_product_name", "cloud_category", "cloud_model", "cloud_uuid", "cloud_online", "cloud_mac", "cloud_product_id", "cloud_status"]:
                        if dev_config.get(res_conf):
                            self.device_data[res_conf] = dev_config.get(res_conf)
                    
                    self.dps_strings = merge_dps_manual_strings(
                        self.device_data.get(CONF_MANUAL_DPS, ""), self.dps_strings
                    )
                    if self.device_data.pop(CONF_ENABLE_ADD_ENTITIES, False):
                        self.editing_device = False
                        user_input[CONF_DEVICE_ID] = dev_id
                        self.device_data.update(
                            {
                                CONF_DEVICE_ID: dev_id,
                                CONF_NODE_ID: self.nodeID,
                                CONF_DPS_STRINGS: self.dps_strings,
                            }
                        )
                        return await self.async_step_pick_entity_type()

                    self.device_data.update(
                        {
                            CONF_DEVICE_ID: dev_id,
                            CONF_NODE_ID: self.nodeID,
                            CONF_DPS_STRINGS: self.dps_strings,
                            CONF_ENTITIES: [],
                        }
                    )

                    if len(user_input[CONF_ENTITIES]) == 0:
                        # If user unchecked all entities.
                        return self.async_abort(reason="no_entities")

                    if user_input[CONF_ENTITIES]:
                        entity_ids = [
                            int(e.split(":")[0]) for e in user_input[CONF_ENTITIES]
                        ]
                        if self.use_template:
                            device_config = self.template_device
                        else:
                            device_config = self.config_entry.data[CONF_DEVICES][dev_id]
                        self.entities = [
                            entity
                            for entity in device_config[CONF_ENTITIES]
                            if int(entity[CONF_ID]) in entity_ids
                        ]
                        return await self.async_step_configure_entity()

                # Get Cloud DPS for comparison if available
                dev_id_to_check = self.selected_device or user_input.get(CONF_DEVICE_ID)
                
                # ULTIMATE FIX: Ensure cloud data is loaded and force pull for this device
                if not self.config_entry.data.get(CONF_NO_CLOUD, True):
                    _LOGGER.info(f"[TUYA-DEBUG] Ensuring cloud devices list is loaded...")
                    await self.cloud_data.async_get_devices_list()
                    cloud_devs = self.cloud_data.device_list # Re-fetch list
                
                if dev_id_to_check in cloud_devs:
                    if not cloud_devs[dev_id_to_check].get(CONF_DPS_STRINGS):
                        _LOGGER.info(f"[TUYA-DEBUG] Pulling functions for {dev_id_to_check} from Cloud...")
                        dps_data = await self.cloud_data.async_get_device_functions(dev_id_to_check)
                        # Re-format strings
                        cloud_devs[dev_id_to_check][CONF_DPS_STRINGS] = dps_string_list({}, dps_data)
                
                cloud_dps = None
                if dev_id_to_check in cloud_devs:
                    cloud_dps = cloud_devs[dev_id_to_check].get(CONF_DPS_STRINGS, [])
                    _LOGGER.info(f"[TUYA-DEBUG] Device {dev_id_to_check}: Found {len(cloud_dps)} Cloud DPs")

                # SIMPLE ASYNC LOGIC WITH SEPARATE STEP
                cloud_dps = None
                if dev_id_to_check in cloud_devs:
                    if not cloud_devs[dev_id_to_check].get(CONF_DPS_STRINGS):
                        _LOGGER.info(f"[TUYA-DEBUG] Pulling functions for {dev_id_to_check} from Cloud...")
                        dps_data = await self.cloud_data.async_get_device_functions(dev_id_to_check)
                        cloud_devs[dev_id_to_check][CONF_DPS_STRINGS] = dps_string_list({}, dps_data)
                    cloud_dps = cloud_devs[dev_id_to_check].get(CONF_DPS_STRINGS, [])

                # Check for duplicate device (same host/IP or same cloud device_id
                # already configured under a different localtuya entry)
                new_host = user_input.get(CONF_HOST, "")
                new_cloud_id = user_input.get(CONF_DEVICE_ID, "")
                # Also get MAC from cloud data if available (factory-reset devices
                # get new cloud IDs but keep the same hardware MAC)
                new_mac_from_cloud = (cloud_devs.get(new_cloud_id, {}).get("mac")
                                      if new_cloud_id else "")
                existing_errors = []
                entries = hass.config_entries.async_entries(DOMAIN)

                def _norm_mac(m):
                    return (m or "").lower().replace(":", "").replace("-", "").replace(" ", "")

                for existing_entry in entries:
                    for existing_dev_id, existing_dev in existing_entry.data.get(
                        CONF_DEVICES, {}
                    ).items():
                        existing_host = existing_dev.get(CONF_HOST, "")
                        existing_name = existing_dev.get(CONF_FRIENDLY_NAME, "")
                        existing_mac = existing_dev.get("mac", "")
                        existing_cloud_id = existing_dev.get("device_id", "")

                        if new_host and existing_host == new_host and existing_dev_id != dev_id:
                            existing_errors.append(
                                f"La IP {new_host} è già configurata per il dispositivo "
                                f'"{existing_name}" (id: {existing_dev_id}).'
                            )
                        if new_cloud_id and existing_cloud_id == new_cloud_id and existing_dev_id != dev_id:
                            existing_errors.append(
                                f"L'ID cloud {new_cloud_id} è già registrato in localtuya "
                                f'come "{existing_name}" (id: {existing_dev_id}).'
                            )
                        # Check MAC match (catches factory-reset devices with new cloud IDs)
                        compare_mac = new_mac_from_cloud or user_input.get("mac", "")
                        if (
                            compare_mac
                            and existing_host
                            and _norm_mac(existing_mac) == _norm_mac(compare_mac)
                            and existing_dev_id != dev_id
                        ):
                            existing_errors.append(
                                f"La MAC {existing_mac} è già configurata per il dispositivo "
                                f'"{existing_name}" con IP {existing_host} (id: {existing_dev_id}). '
                                "Lo stesso dispositivo fisico non può apparire due volte."
                            )

                if existing_errors:
                    _LOGGER.warning("Duplicate device blocked: %s", existing_errors)
                    errors["base"] = "duplicate_device"
                    placeholders["device_info"] = " ".join(existing_errors)
                    return self.async_show_form(
                        step_id="configure_device",
                        data_schema=schema_suggested_values(DEVICE_SCHEMA, **defaults),
                        errors=errors,
                        description_placeholders=placeholders,
                    )

                if not hasattr(self, "_validate_task"):
                    self._validate_task = self.hass.async_create_task(
                        validate_input(
                            self.localtuya_data, 
                            user_input, 
                            cloud_dps=cloud_dps
                        )
                    )
                
                return await self.async_step_connecting()

            except (CannotConnect, InvalidAuth, EmptyDpsList):
                errors["base"] = "cannot_connect"
            except (OSError, ValueError, pytuya.parser.DecodeError) as ex:
                _LOGGER.debug("Unexpected exception: %s", ex)
                placeholders["ex"] = str(ex)
                errors["base"] = "unknown"
            except Exception as ex:
                _LOGGER.debug("Unexpected exception: %s", ex)
                raise ex

        defaults = {}
        if self.editing_device:
            # If selected device exists as a config entry, load config from it
            defaults = (
                self.device_data
                if self.use_template
                else self.config_entry.data[CONF_DEVICES][dev_id].copy()
            )

            self.nodeID = defaults.get(CONF_NODE_ID, None)
            placeholders["for_device"] = f" for device `{dev_id}`"
            if self.nodeID:
                placeholders.update(
                    {"for_device": f"for Sub-Device `{dev_id}.NodeID {self.nodeID}`"}
                )
            if dev_id in cloud_devs:
                cloud_local_key = cloud_devs[dev_id].get(CONF_LOCAL_KEY)
                if defaults[CONF_LOCAL_KEY] != cloud_local_key:
                    _LOGGER.info(
                        "New local_key detected: new %s vs old %s",
                        cloud_local_key,
                        defaults[CONF_LOCAL_KEY],
                    )
                    defaults[CONF_LOCAL_KEY] = cloud_devs[dev_id].get(CONF_LOCAL_KEY)
                    note = "\nNOTE: a new local_key has been retrieved using cloud API"
                    placeholders = {"for_device": f" for device `{dev_id}`.{note}"}
                    if self.nodeID:
                        placeholders = {
                            "for_device": f" for sub-device `{dev_id}.\nNodeID {self.nodeID}.{note}`"
                        }
            schema = schema_suggested_values(options_schema(self.entities), **defaults)
        else:
            # user_in will restore input if an error occurred instead of clears all fields.
            user_in = user_input or {}
            defaults[CONF_PROTOCOL_VERSION] = user_in.get(CONF_PROTOCOL_VERSION, "auto")
            defaults[CONF_HOST] = user_in.get(CONF_HOST, "")
            defaults[CONF_DEVICE_ID] = user_in.get(CONF_DEVICE_ID, "")
            defaults[CONF_LOCAL_KEY] = user_in.get(CONF_LOCAL_KEY, "")
            defaults[CONF_FRIENDLY_NAME] = user_in.get(CONF_FRIENDLY_NAME, "")
            defaults[CONF_NODE_ID] = user_in.get(CONF_NODE_ID, "")

            if defaults[CONF_DEVICE_ID] in [cloud_devs, self.selected_device]:
                dev_id = defaults[CONF_DEVICE_ID]

            if dev_id is not None and dev_id in self.discovered_devices:
                # Insert default values from discovery and cloud if present
                device = self.discovered_devices.get(dev_id, {})
                defaults[CONF_HOST] = device.get(CONF_TUYA_IP)
                defaults[CONF_DEVICE_ID] = device.get(CONF_TUYA_GWID)
                defaults[CONF_PROTOCOL_VERSION] = device.get(CONF_TUYA_VERSION)
                defaults[CONF_NODE_ID] = device.get(CONF_NODE_ID, None)

            if dev_id in cloud_devs:
                defaults[CONF_LOCAL_KEY] = cloud_devs[dev_id].get(CONF_LOCAL_KEY)
                defaults[CONF_FRIENDLY_NAME] = cloud_devs[dev_id].get(CONF_NAME)
                # Add MAC address from cloud if available
                if cloud_devs[dev_id].get("mac"):
                    defaults[CONF_MAC] = cloud_devs[dev_id]["mac"]
                # Add cloud IP if available
                if cloud_devs[dev_id].get("ip"):
                    defaults["cloud_ip"] = cloud_devs[dev_id]["ip"]
                # Add product name and category if available
                if cloud_devs[dev_id].get("product_name"):
                    defaults["cloud_product_name"] = cloud_devs[dev_id]["product_name"]
                if cloud_devs[dev_id].get("category"):
                    defaults["cloud_category"] = cloud_devs[dev_id]["category"]
                if cloud_devs[dev_id].get("model"):
                    defaults["cloud_model"] = cloud_devs[dev_id]["model"]
                if cloud_devs[dev_id].get("uuid"):
                    defaults["cloud_uuid"] = cloud_devs[dev_id]["uuid"]
                if cloud_devs[dev_id].get("online") is not None:
                    defaults["cloud_online"] = cloud_devs[dev_id]["online"]
                if cloud_devs[dev_id].get("category"):
                    defaults["cloud_category"] = cloud_devs[dev_id]["category"]
                if cloud_devs[dev_id].get("product_id"):
                    defaults["cloud_product_id"] = cloud_devs[dev_id]["product_id"]
                if cloud_devs[dev_id].get("product_name"):
                    defaults["cloud_product_name"] = cloud_devs[dev_id]["product_name"]
                if cloud_devs[dev_id].get("status"):
                    defaults["cloud_status"] = cloud_devs[dev_id]["status"]
                if cloud_devs[dev_id].get("model"):
                    defaults["cloud_model"] = cloud_devs[dev_id]["model"]
                if cloud_devs[dev_id].get("uuid"):
                    defaults["cloud_uuid"] = cloud_devs[dev_id]["uuid"]
                if cloud_devs[dev_id].get("online") is not None:
                    defaults["cloud_online"] = cloud_devs[dev_id]["online"]
                if cloud_devs[dev_id].get("category"):
                    defaults["cloud_category"] = cloud_devs[dev_id]["category"]
                if cloud_devs[dev_id].get("product_id"):
                    defaults["cloud_product_id"] = cloud_devs[dev_id]["product_id"]
                if cloud_devs[dev_id].get("product_name"):
                    defaults["cloud_product_name"] = cloud_devs[dev_id]["product_name"]
                if cloud_devs[dev_id].get("status"):
                    defaults["cloud_status"] = cloud_devs[dev_id]["status"]
                if cloud_devs[dev_id].get("model"):
                    defaults["cloud_model"] = cloud_devs[dev_id]["model"]
                if cloud_devs[dev_id].get("uuid"):
                    defaults["cloud_uuid"] = cloud_devs[dev_id]["uuid"]
                if cloud_devs[dev_id].get("online") is not None:
                    defaults["cloud_online"] = cloud_devs[dev_id]["online"]
                if cloud_devs[dev_id].get("category"):
                    defaults["cloud_category"] = cloud_devs[dev_id]["category"]
                if cloud_devs[dev_id].get("product_id"):
                    defaults["cloud_product_id"] = cloud_devs[dev_id]["product_id"]
                if cloud_devs[dev_id].get("product_name"):
                    defaults["cloud_product_name"] = cloud_devs[dev_id]["product_name"]
                if cloud_devs[dev_id].get("status"):
                    defaults["cloud_status"] = cloud_devs[dev_id]["status"]
                if cloud_devs[dev_id].get("model"):
                    defaults["cloud_model"] = cloud_devs[dev_id]["model"]
                if cloud_devs[dev_id].get("uuid"):
                    defaults["cloud_uuid"] = cloud_devs[dev_id]["uuid"]
                if cloud_devs[dev_id].get("online") is not None:
                    defaults["cloud_online"] = cloud_devs[dev_id]["online"]
                if cloud_devs[dev_id].get("category"):
                    defaults["cloud_category"] = cloud_devs[dev_id]["category"]
                if cloud_devs[dev_id].get("product_id"):
                    defaults["cloud_product_id"] = cloud_devs[dev_id]["product_id"]
                if cloud_devs[dev_id].get("product_name"):
                    defaults["cloud_product_name"] = cloud_devs[dev_id]["product_name"]
                if cloud_devs[dev_id].get("status"):
                    defaults["cloud_status"] = cloud_devs[dev_id]["status"]

            # Update local IP from discovery if available (fixes cloud IP showing instead of local)
            if dev_id in self.discovered_devices:
                device = self.discovered_devices.get(dev_id, {})
                if device.get(CONF_TUYA_IP):
                    defaults[CONF_HOST] = device.get(CONF_TUYA_IP)

            schema = schema_suggested_values(DEVICE_SCHEMA, **defaults)

            placeholders["for_device"] = ""

        return self.async_show_form(
            step_id="configure_device",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_pick_entity_type(self, user_input=None):
        """Handle asking if user wants to add another entity."""
        if user_input is not None:
            if user_input.get(NO_ADDITIONAL_ENTITIES):
                config = {
                    **self.device_data,
                    CONF_DPS_STRINGS: self.dps_strings,
                    CONF_ENTITIES: self.entities,
                }
                dev_id = self.device_data.get(CONF_DEVICE_ID)
                new_data = self.config_entry.data.copy()
                new_data[CONF_DEVICES].update({dev_id: config})
                return self._update_entry(new_data)
            if user_input.get(USE_TEMPLATE):
                return await self.async_step_choose_template()
            self.selected_platform = user_input[PLATFORM_TO_ADD]
            return await self.async_step_configure_entity()
        schema = vol.Schema({vol.Required(PLATFORM_TO_ADD, default='switch'): col_to_select(PLATFORMS)})
        if self.selected_platform is not None:
            schema = schema.extend({vol.Required(NO_ADDITIONAL_ENTITIES, default=True): bool})
        return self.async_show_form(step_id='pick_entity_type', data_schema=schema)

    async def async_step_choose_template(self, user_input=None):
        """Handle asking which templates to use"""
        if user_input is not None:
            self.use_template = True
            filename = user_input.get(TEMPLATES)
            _config = await self.hass.async_add_executor_job(
                templates.import_config, filename
            )
            dev_conf = self.device_data
            dev_conf[CONF_ENTITIES] = _config
            dev_conf[CONF_DPS_STRINGS] = self.dps_strings
            dev_conf[CONF_NODE_ID] = self.nodeID
            self.device_data = dev_conf

            self.entities = dev_conf[CONF_ENTITIES]
            self.template_device = self.device_data
            self.editing_device = True
            return await self.async_step_configure_device()
        templates_list = await self.hass.async_add_executor_job(
            templates.list_templates
        )
        schema = vol.Schema(
            {vol.Required(TEMPLATES): col_to_select(templates_list, custom_value=True)}
        )
        return self.async_show_form(step_id="choose_template", data_schema=schema)

    async def async_step_entity(self, user_input=None):
        """Manage entity settings."""
        errors = {}
        if user_input is not None:
            entity = strip_dps_values(user_input, self.dps_strings)
            entity[CONF_ID] = self.current_entity[CONF_ID]
            entity[CONF_PLATFORM] = self.current_entity[CONF_PLATFORM]
            self.device_data[CONF_ENTITIES].append(entity)
            if len(self.entities) == len(self.device_data[CONF_ENTITIES]):
                return self._update_entry(self.device_data)

        schema = await platform_schema(
            self.hass, self.current_entity[CONF_PLATFORM], self.dps_strings, False
        )
        return self.async_show_form(
            step_id="entity",
            errors=errors,
            data_schema=schema_suggested_values(schema, **self.current_entity),
            description_placeholders={
                "id": int(self.current_entity[CONF_ID]),
                "platform": self.current_entity[CONF_PLATFORM],
            },
        )

    async def async_step_configure_entity(self, user_input=None):
        """Manage entity settings."""
        errors = {}
        if user_input is not None:
            if self.editing_device:
                entity = strip_dps_values(user_input, self.dps_strings)
                entity[CONF_ID] = self.current_entity[CONF_ID]
                entity[CONF_PLATFORM] = self.current_entity[CONF_PLATFORM]
                entity[CONF_ICON] = self.current_entity.get(CONF_ICON, "")
                self.device_data[CONF_ENTITIES].append(entity)
                if len(self.entities) == len(self.device_data[CONF_ENTITIES]):
                    # finished editing device. Let's store the new config entry....
                    dev_id = self.device_data[CONF_DEVICE_ID]
                    new_data = self.config_entry.data.copy()
                    entry_id = self.config_entry.entry_id
                    # Removing the unwanted entities.
                    entitesNames = [
                        name.get(CONF_FRIENDLY_NAME)
                        for name in self.device_data[CONF_ENTITIES]
                    ]
                    ent_reg = er.async_get(self.hass)
                    reg_entities = {
                        ent.unique_id: ent.entity_id
                        for ent in er.async_entries_for_config_entry(ent_reg, entry_id)
                        if dev_id in ent.unique_id
                        and ent.original_name not in entitesNames
                    }
                    for entity_id in reg_entities.values():
                        ent_reg.async_remove(entity_id)

                    new_data[CONF_DEVICES][dev_id] = self.device_data
                    return self._update_entry(new_data)
            else:
                user_input[CONF_PLATFORM] = self.selected_platform
                self.entities.append(strip_dps_values(user_input, self.dps_strings))
                # new entity added. Let's check if there are more left...
                user_input = None
                if len(self.available_dps_strings()) == 0:
                    user_input = {NO_ADDITIONAL_ENTITIES: True}
                return await self.async_step_pick_entity_type(user_input)

        if self.editing_device:
            schema = await platform_schema(
                self.hass, self.current_entity[CONF_PLATFORM], self.dps_strings, False
            )
            schema = schema_suggested_values(schema, **self.current_entity)
            placeholders = {
                "entity": f"entity with DP {int(self.current_entity[CONF_ID])}",
                "platform": self.current_entity[CONF_PLATFORM],
            }
        else:
            available_dps = self.available_dps_strings()
            schema = await platform_schema(
                self.hass, self.selected_platform, available_dps
            )
            placeholders = {
                "entity": "an entity",
                "platform": self.selected_platform,
            }

        return self.async_show_form(
            step_id="configure_entity",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_confirm(self, msg: str, confirm_callback: Coroutine = None):
        """Create a confirmation config flow page. If submitted, the `confirm_callback` will be called."""
        if confirm_callback:
            self._confirm_callback = confirm_callback

        placeholders = {}
        placeholders["message"] = msg

        if not msg:
            return self._confirm_callback()

        return self.async_show_form(
            step_id="confirm", description_placeholders=placeholders
        )

        # menu = ["confirm", "init"]
        # return self.async_show_menu(
        #     step_id="confirm", menu_options=menu, description_placeholders=placeholders
        # )

    @callback
    def _update_entry(self, new_data, target_obj="", new_title=""):
        """Update entry data and save etnry,"""
        _data = copy.deepcopy(dict(self.config_entry.data))
        if target_obj:
            _data[target_obj].update(new_data)
        else:
            _data.update(new_data)
        _data[ATTR_UPDATED_AT] = str(int(time.time() * 1000))

        self.hass.config_entries.async_update_entry(
            self.config_entry, data=_data, title=new_title or self.config_entry.title
        )
        return self.async_create_entry(title=new_title, data={})

    def available_dps_strings(self):
        """Return list of DPs use by the device's entities."""
        available_dps = []
        used_dps = [str(entity[CONF_ID]) for entity in self.entities]
        for dp_string in self.dps_strings:
            dp = dp_string.split(" ")[0]
            if dp not in used_dps:
                available_dps.append(dp_string)
        return available_dps

    @property
    def current_entity(self):
        """Existing configuration for entity currently being edited."""
        return self.entities[len(self.device_data[CONF_ENTITIES])]


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class EmptyDpsList(exceptions.HomeAssistantError):
    """Error to indicate no datapoints found."""


async def setup_localtuya_devices(
    hass: HomeAssistant,
    localtuya_data: HassLocalTuyaData,
    discovered_devices: dict,
    devices_cloud_data: dict,
    log_fails=False,
    progress_callback: Callable[[int, int, str], Any] | None = None,
):
    """Return a dict of configured devices ready to import into devices data."""
    devices_cfg = []
    devices = {}
    fails = {}

    async def report_progress(current: int, total: int, status: str) -> None:
        if not progress_callback:
            return
        try:
            result = progress_callback(current, total, status)
            if asyncio.iscoroutine(result):
                await result
        except Exception as ex:
            _LOGGER.debug("Failed to update mass configure progress: %s", ex)

    def update_fails(dev_id: str, reason: str, msg: str = None):
        name = devices_cloud_data[dev_id].get(CONF_NAME, dev_id)
        fails.update({dev_id: {"name": name, "reason": reason}})
        if log_fails:
            msg = f"[ name: {name} — id: {dev_id} — reason: {reason or repr(reason)}]"
            _LOGGER.warning(f"Failed to configure device: {msg}")

    entries = hass.config_entries.async_entries(DOMAIN)
    configured_devices = []
    for entry in entries:
        for dev_id in entry.data[CONF_DEVICES].keys():
            configured_devices.append(dev_id)

    for dev_id, data in discovered_devices.items():
        if dev_id in configured_devices:
            continue
        if dev_cloud_data := devices_cloud_data.get(dev_id):
            device_data = {
                CONF_FRIENDLY_NAME: dev_cloud_data.get(CONF_NAME, dev_id),
                CONF_DEVICE_ID: dev_id,
                CONF_HOST: data[CONF_TUYA_IP],
                CONF_LOCAL_KEY: dev_cloud_data.get(CONF_LOCAL_KEY),
                CONF_PROTOCOL_VERSION: data[CONF_TUYA_VERSION],
                CONF_ENABLE_DEBUG: False,
                CONF_NODE_ID: dev_cloud_data.get(CONF_NODE_ID),
                CONF_MODEL: dev_cloud_data.get(CONF_MODEL),
                CONF_PRODUCT_KEY: data.get("productKey"),
            }
            if sub_gwid := data.get(CONF_GATEWAY_ID):
                device_data.update({CONF_GATEWAY_ID: sub_gwid})

            devices_cfg.append(device_data)

    total = len(devices_cfg)
    await report_progress(0, total, f"Avvio configurazione automatica: 0/{total}")

    if total == 0:
        await report_progress(0, 0, "Nessun dispositivo disponibile da configurare")
        return devices, fails

    for index, device_data in enumerate(devices_cfg, start=1):
        dev_id = device_data[CONF_DEVICE_ID]
        name = device_data.get(CONF_FRIENDLY_NAME, dev_id)

        await report_progress(
            index - 1,
            total,
            f"Tentativo {index}/{total}: {name}",
        )

        try:
            valid_data = await validate_input(localtuya_data, device_data)
        except Exception as ex:
            update_fails(dev_id, ex)
            await report_progress(
                index,
                total,
                f"Tentativo {index}/{total} fallito: {name}",
            )
            continue

        configured_device = {**device_data, **valid_data}
        category = devices_cloud_data[dev_id].get(TUYA_CATEGORY)
        configured_device[DEVICE_CLOUD_DATA] = devices_cloud_data[dev_id]

        dev_entities = None
        if category and configured_device.get(CONF_DPS_STRINGS):
            dev_entities = gen_localtuya_entities(configured_device, category)

        if not dev_entities:
            update_fails(dev_id, f"no configured entities: {dev_entities} - {category}")
            await report_progress(
                index,
                total,
                f"Nessuna entità trovata ({index}/{total}): {name}",
            )
            continue

        configured_device.pop(DEVICE_CLOUD_DATA, None)
        configured_device[CONF_ENTITIES] = dev_entities
        devices[dev_id] = configured_device

        await report_progress(
            index,
            total,
            f"Configurato {index}/{total}: {name}",
        )

    await report_progress(
        total,
        total,
        f"Configurazione completata: {len(devices)} ok, {len(fails)} falliti",
    )

    return devices, fails


async def discover_devices() -> tuple[dict[str, dict], dict[str, str]]:
    """Start discovering Tuya devices within the network"""
    errors = {}
    discovered_devices = {}
    try:
        discovered_devices = await discover()
    except OSError as ex:
        if ex.errno == errno.EADDRINUSE:
            errors["base"] = "address_in_use"
        else:
            errors["base"] = "discovery_failed"
    except Exception as ex:
        _LOGGER.exception("discovery failed: %s", ex)
        errors["base"] = "discovery_failed"
    return discovered_devices, errors


def devices_schema(
    discovered_devices, cloud_devices_list, add_custom_device=True, existed_devices={}
):
    """Create schema for devices step."""
    known_devices = {}
    devices = {}
    for dev_id, dev_host in discovered_devices.items():
        dev_name = dev_id
        provenance = "ID"
        # Handle both formats: dict with CONF_TUYA_IP (discovery) or string IP (edit mode)
        if isinstance(dev_host, dict):
            host_str = dev_host.get(CONF_TUYA_IP, "")
            # Try to get name from device data dict (cloud name or fallback)
            dev_name = dev_host.get("name", dev_id)
            if "name" in dev_host and dev_host["name"] != dev_id:
                provenance = "cloud"
        else:
            host_str = str(dev_host)
        
        # when editing devices get INFOS from stored!.
        if not add_custom_device and dev_id in existed_devices.keys():
            dev_name = existed_devices[dev_id].get(CONF_FRIENDLY_NAME, dev_id)
            provenance = "config"
        elif dev_id in cloud_devices_list.keys():
            dev_name = cloud_devices_list[dev_id][CONF_NAME]
            provenance = "cloud"

            known_devices[f"{dev_name} ({host_str}) [{provenance}]"] = dev_id
            continue

        _LOGGER.debug("devices_schema: device=%s name=%s host=%s provenance=%s",
                      dev_id, dev_name, host_str, provenance)
        devices[f"{dev_name} ({host_str}) [{provenance}]"] = dev_id

    known_devices = dict(sorted(known_devices.items()))
    devices = {**known_devices, **devices}
    if add_custom_device:
        devices.update(CUSTOM_DEVICE)
    else:  # Sort devices in edit mode.
        devices = dict(sorted(devices.items()))

    schema = vol.Schema(
        {
            vol.Required(SELECTED_DEVICE): col_to_select(devices),
        }
    )

    return schema.extend(MASS_CONFIGURE_SCHEMA) if known_devices else schema


def mergeDevicesList(localList: dict, cloudList: dict, addSubDevices=True) -> dict:
    """Merge CloudDevices with Discovered LocalDevices (in specific ways)!"""
    # try Get SubDevices.
    newList = localList.copy()
    for _devID, _devData in cloudList.items():
        try:
            is_online = _devData.get("online", None)
            sub_device = _devData.get(CONF_NODE_ID, False)
            # We skip offline devices and already merged devices.
            if not is_online or _devID in localList:
                continue
            # Make sure the device isn't already in localList.
            if addSubDevices and sub_device:
                # infrared are ir remote sub-devices
                if _devData.get(TUYA_CATEGORY, "").startswith("infrared"):
                    continue

                gateway = get_gateway_by_deviceid(_devID, cloudList)
                local_gw = localList.get(gateway.id)
                if local_gw:
                    # Create a data for sub_device [cloud and local gateway] to merge it with discovered devices.
                    dev_data = {
                        _devID: {
                            CONF_TUYA_IP: local_gw.get(CONF_TUYA_IP),
                            CONF_TUYA_GWID: _devID,
                            CONF_TUYA_VERSION: local_gw.get(CONF_TUYA_VERSION, "auto"),
                            CONF_NODE_ID: _devData.get(CONF_NODE_ID, None),
                            CONF_GATEWAY_ID: local_gw.get(CONF_TUYA_GWID),
                        }
                    }
                    newList.update(dev_data)
            # Also add regular cloud devices (not sub-devices) that weren't discovered locally
            elif not sub_device:
                # Create data for regular cloud device
                dev_data = {
                    _devID: {
                        CONF_TUYA_IP: _devData.get("ip", ""),  # Use cloud IP (might be public)
                        CONF_TUYA_GWID: _devID,
                        CONF_TUYA_VERSION: _devData.get("version", "auto"),
                        CONF_NODE_ID: None,
                    }
                }
                newList.update(dev_data)
        except Exception as ex:
            _LOGGER.debug(f"An error occurred while trying to pull sub-devices {ex}")
            continue
    return newList


def options_schema(entities):
    """Create schema for options."""
    entity_names = [
        f"{entity[CONF_ID]}: {entity[CONF_FRIENDLY_NAME]}" for entity in entities
    ]
    return vol.Schema(
        {
            vol.Required(CONF_FRIENDLY_NAME): cv.string,
            vol.Required(CONF_HOST): cv.string,
            vol.Required(CONF_LOCAL_KEY): cv.string,
            vol.Required(CONF_PROTOCOL_VERSION, default="3.3"): col_to_select(
                sorted(SUPPORTED_PROTOCOL_VERSIONS)
            ),
            vol.Required(CONF_ENABLE_DEBUG, default=False): bool,
            vol.Optional(CONF_SCAN_INTERVAL): int,
            vol.Optional(CONF_MANUAL_DPS): cv.string,
            vol.Optional(CONF_RESET_DPIDS): cv.string,
            vol.Optional(CONF_DEVICE_SLEEP_TIME): int,
            vol.Required(
                CONF_ENTITIES, description={"suggested_value": entity_names}
            ): cv.multi_select(entity_names),
            # col_to_select(entity_names, multi_select=True)
            vol.Required(CONF_ENABLE_ADD_ENTITIES, default=False): bool,
            vol.Optional(EXPORT_CONFIG, default=False): bool,
            # Cloud info fields (read-only display)
            vol.Optional("cloud_ip"): cv.string,
            vol.Optional("cloud_product_name"): cv.string,
            vol.Optional("cloud_category"): cv.string,
            vol.Optional("cloud_model"): cv.string,
            vol.Optional("cloud_uuid"): cv.string,
            vol.Optional("cloud_online"): cv.string,
            vol.Optional("cloud_mac"): cv.string,
        }
    )


def schema_suggested_values(schema: vol.Schema, **defaults):
    """Returns a copy of the schema with suggested values added to field descriptions."""
    new_schema = {}
    for field, field_type in schema.schema.items():
        new_field = copy.copy(field)

        # We don't want to overwrite existing suggested values.
        if field.schema in defaults and (
            not field.description or "suggested_value" not in field.description
        ):
            new_field.description = {"suggested_value": defaults[field]}

        new_schema[new_field] = field_type
    return vol.Schema(new_schema)


def dps_string_list(dps_data: dict[str, dict], cloud_dp_codes: dict[str, dict]) -> list:
    """Return list of friendly DPS values with cloud-first precedence."""
    dps_data = dps_data or {}
    cloud_dp_codes = cloud_dp_codes or {}

    labels_by_dp: dict[str, str] = {}

    # 1) Cloud-first: if cloud knows a DP, use cloud code as canonical metadata.
    for dp, func in cloud_dp_codes.items():
        dp_str = str(dp)
        code = (func or {}).get("code", "cloud")
        if dp_str in dps_data:
            labels_by_dp[dp_str] = f"{dp_str} ( code: {code} , value: {dps_data[dp_str]} )"
        else:
            labels_by_dp[dp_str] = f"{dp_str} ( code: {code} , cloud pull )"

    # 2) Local fallback: only for DPs unknown to cloud.
    for dp, value in dps_data.items():
        dp_str = str(dp)
        if dp_str not in labels_by_dp:
            labels_by_dp[dp_str] = f"{dp_str} (value: {value})"

    return sorted(labels_by_dp.values(), key=lambda i: int(i.split()[0]))


def gen_dps_strings():
    """Generate list of DPS values."""
    return [f"{dp} (value: ?)" for dp in range(1, 256)]


def strip_dps_values(user_input, dps_strings):
    """Remove values and keep only index for DPS config items."""
    stripped = {}
    for field, value in user_input.items():
        if value in dps_strings:
            stripped[field] = int(user_input[field].split(" ")[0])
        else:
            stripped[field] = user_input[field]
    return stripped


def merge_dps_manual_strings(manual_dps: list, dps_strings: list):
    """Split manual_dps by comma and assign -1 as default value. Return merged with dps string."""
    manual_list = []
    avaliable_dps = [dp.split(" ")[0] for dp in dps_strings]

    for dp in manual_dps.split(","):
        dp = dp.strip()
        if dp.isdigit() and dp not in avaliable_dps and dp != "0":
            manual_list.append(f"{dp} ( value: -1 )")

    return sorted(dps_strings + manual_list, key=lambda i: int(i.split(" ")[0]))


async def platform_schema(
    hass: HomeAssistant, platform, dps_strings, allow_id=True, yaml=False
):
    """Generate input validation schema for a platform."""
    # decide default value of device by platform.
    schema = {}
    if yaml:
        # In YAML mode we force the specified platform to match flow schema
        schema[vol.Required(CONF_PLATFORM)] = col_to_select([platform])
    if allow_id:
        schema[vol.Required(CONF_ID)] = col_to_select(dps_strings, is_dps=True)
    schema[vol.Optional(CONF_FRIENDLY_NAME, default="")] = vol.Any(None, cv.string)
    schema[
        vol.Required(CONF_ENTITY_CATEGORY, default=str(default_category(platform)))
    ] = col_to_select(ENTITY_CATEGORY)

    plat_schema = await hass.async_add_import_executor_job(
        flow_schema, platform, dps_strings
    )

    return vol.Schema(schema).extend(plat_schema)


def default_category(_platform):
    """Auto Select default category depends on the platform."""
    if any(_platform in i for i in DEFAULT_CATEGORIES["CONTROL"]):
        return None
    elif any(_platform in i for i in DEFAULT_CATEGORIES["CONFIG"]):
        return EntityCategory.CONFIG
    elif any(_platform in i for i in DEFAULT_CATEGORIES["DIAGNOSTIC"]):
        return EntityCategory.DIAGNOSTIC
    else:
        return None


def flow_schema(platform, dps_strings):
    """Return flow schema for a specific platform."""
    integration_module = ".".join(__name__.split(".")[:-1])
    return import_module("." + platform, integration_module).flow_schema(dps_strings)


async def validate_input(entry_runtime: HassLocalTuyaData, data, cloud_dps=None, async_progress_callback=None):
    """Validate the user input allows us to connect."""
    logger = pytuya.ContextualLogger()
    logger.set_logger(_LOGGER, data[CONF_DEVICE_ID], True, data[CONF_FRIENDLY_NAME])
    
    _LOGGER.debug(f"[validate_input] Starting validation for device {data.get(CONF_DEVICE_ID)} at host {data.get(CONF_HOST)}")

    detected_dps = {}
    error = None
    interface = None
    reset_ids = None
    close = True
    bypass_connection = False  # On users risk, only used for low-power power devices
    bypass_handshake = False  # In-case device is passive.

    # expected_count is currently unused, but keep as a hint for timeouts.
    expected_count = len(cloud_dps) if cloud_dps else 1
    cid = data.get(CONF_NODE_ID, None)
    localtuya_devices = entry_runtime.devices
    try:
        conf_protocol = data[CONF_PROTOCOL_VERSION]
        auto_protocol = conf_protocol == "auto"
        # If sub device we will search if gateway is existed if not create new connection.
        if (
            cid
            and (existed_interface := localtuya_devices.get(data[CONF_HOST]))
            and existed_interface.connected
            and not existed_interface.is_connecting
        ):
            interface = existed_interface._interface
            close = False
        else:
            # If 'auto' will be loop through supported protocols.
            for ver in SUPPORTED_PROTOCOL_VERSIONS:
                try:
                    version = ver if auto_protocol else conf_protocol
                    logger.info(f"Connecting with protocol version: {version}")

                    # Increased timeout logic based on expected DPS
                    timeout = 15 if not cloud_dps else 30
                    async with asyncio.timeout(timeout):
                        if async_progress_callback:
                            async_progress_callback(1, 5 if cloud_dps else 3, timeout)

                        interface = await pytuya.connect(
                            data[CONF_HOST],
                            data[CONF_DEVICE_ID],
                            data[CONF_LOCAL_KEY],
                            float(version),
                            data[CONF_ENABLE_DEBUG],
                        )
                        logger.info(f"Connected - detecting DPS (expected: {expected_count})")
                        # Wake up sequence
                        try:
                            await interface.heartbeat()
                            await asyncio.sleep(1.0)
                            await interface.update_dps()
                            await asyncio.sleep(1.0)
                        except:
                            pass

                        # Enhanced retry loop
                        max_attempts = 5 if cloud_dps else 3
                        for attempt in range(max_attempts):
                            if async_progress_callback:
                                async_progress_callback(attempt + 1, max_attempts, timeout)
                            logger.info(f"[TUYA-DEBUG] DP Discovery attempt {attempt + 1}/{max_attempts}...")
                            current_scan = await interface.detect_available_dps(cid=cid)
                            if current_scan:
                                detected_dps.update(current_scan)
                                logger.info(f"[TUYA-DEBUG] Found {len(current_scan)} DPs. Total: {len(detected_dps)}")

                            if len(detected_dps) >= expected_count:
                                logger.info("[TUYA-DEBUG] All expected DPs found!")
                                break

                            await asyncio.sleep(1.5 * (attempt + 1)) # Incremental wait

                    # Break the loop if input isn't auto.
                    if not auto_protocol:
                        break
                    # If Auto: using DPS detected we will assume this is the correct version if dps found.
                    if len(detected_dps) > 0:
                        # Set the conf_protocol to the worked version to return it and update self.device_data.
                        logger.info(f"[TUYA-DEBUG] Detected DPS: {detected_dps}")
                        conf_protocol = version
                        break

                # If connection to host is failed raise wrong address.
                except (OSError, ValueError) as ex:
                    logger.error(f"[TUYA-DEBUG] Connection failed! {ex}")
                    error = ex
                    break
                except:
                    continue
                finally:
                    if not auto_protocol and data.get(CONF_DEVICE_SLEEP_TIME, 0) > 0:
                        logger.info("[TUYA-DEBUG] Low-power device configured — handshake skipped")
                        bypass_connection = True
                    if not error and not interface:
                        error = InvalidAuth

        if conf_reset_dpids := data.get(CONF_RESET_DPIDS):
            reset_ids_str = conf_reset_dpids.split(",")
            reset_ids = [int(reset_id.strip()) for reset_id in reset_ids_str]
            logger.info("[TUYA-DEBUG] Reset DPIDs configured: %s (%s)", conf_reset_dpids, reset_ids)
        try:
            # If reset dpids set - then assume reset is needed before status.
            if (reset_ids is not None) and (len(reset_ids) > 0):
                logger.debug("[TUYA-DEBUG] Resetting command for DP IDs: %s", reset_ids)
                # Assume we want to request status updated for the same set of DP_IDs as the reset ones.
                interface.set_updatedps_list(reset_ids)

                # Reset the interface
                await interface.reset(reset_ids, cid=cid)

            # Detect any other non-manual DPS strings.  If the local DP query
            # already timed out and we have cloud DPS, do not issue another
            # unbounded local query: some devices negotiate the session but
            # reject DP_QUERY_NEW, which otherwise leaves the config flow stuck.
            if not detected_dps and not (error and cloud_dps):
                async with asyncio.timeout(10):
                    detected_dps = await interface.detect_available_dps(cid=cid)

        except (ValueError, pytuya.parser.DecodeError) as ex:
            error = ex
        except Exception as ex:
            logger.info(f"[TUYA-DEBUG] No DPS able to be detected {ex}")
            detected_dps = {}

        # if manual DPs are set, merge these.
        # detected_dps_device used to prevent user from bypass handshake manual dps.
        detected_dps_device = detected_dps.copy()
        
        # If Cloud DPS list is provided by caller, deterministically merge it into detected_dps.
        # We only need DP IDs here; values are informational.
        if cloud_dps:
            cloud_dp_ids: set[str] = set()
            for dp_str in cloud_dps:
                try:
                    cloud_dp_ids.add(str(dp_str).split(" ")[0])
                except Exception:
                    continue

            added_count = 0
            for dp_id in cloud_dp_ids:
                if dp_id not in detected_dps:
                    detected_dps[dp_id] = -1
                    added_count += 1

            logger.info(
                "[TUYA-DEBUG] DISCOVERY SUMMARY: %s DPs found locally, %s DPs added from cloud (caller). Total: %s",
                len(detected_dps_device),
                added_count,
                len(detected_dps),
            )

        logger.debug("[TUYA-DEBUG] Detected DPS: %s", detected_dps)
        if CONF_MANUAL_DPS in data:
            manual_dps_list = [dps.strip() for dps in data[CONF_MANUAL_DPS].split(",")]
            logger.debug(
                "Manual DPS Setting: %s (%s)", data[CONF_MANUAL_DPS], manual_dps_list
            )
            # merge the lists
            for new_dps in manual_dps_list + (reset_ids or []):
                # If the DPS not in the detected dps list, then add with a
                # default value indicating that it has been manually added
                if str(new_dps) == "0":
                    bypass_handshake = True
                    continue
                if str(new_dps) not in detected_dps:
                    detected_dps[new_dps] = -1

    except (ConnectionRefusedError, ConnectionResetError) as ex:
        raise CannotConnect from ex
    except (OSError, ValueError, pytuya.parser.DecodeError) as ex:
        error = ex
    finally:
        if interface and close:
            await interface.close()

    # Cloud DP mapping for labels/codes (used only to enrich UI labels).
    cloud_dp_codes = {}
    cloud_data = entry_runtime.cloud_data
    dev_id = data.get(CONF_DEVICE_ID)
    
    _LOGGER.info(f"[CL-DEBUG] Checking cloud data for device {dev_id}")
    
    if dev_id in cloud_data.device_list:
        _LOGGER.info(f"[CL-DEBUG] Device {dev_id} FOUND in cloud device list")
        cloud_dp_codes = await cloud_data.async_get_device_functions(dev_id)
        _LOGGER.info(f"[CL-DEBUG] cloud_dp_codes result: {cloud_dp_codes}")
    else:
        _LOGGER.warning(f"[CL-DEBUG] Device {dev_id} NOT FOUND in cloud list. Available: {list(cloud_data.device_list.keys())}")

    # Indicate an error if no datapoints found as the rest of the flow
    # won't work in this case
    if not bypass_connection and error and not detected_dps:
        raise error
    # If bypass handshake. otherwise raise failed to make handshake with device.
    # --- Cloud: We will use the DPS found on cloud if exists.
    # --- No cloud: user will have to input the DPS manually.
    if not detected_dps_device and not (
        (cloud_dp_codes or detected_dps) and bypass_handshake
    ):
        _LOGGER.warning("No DPS detected, but allowing registration as requested by user.")
        # We ensure detected_dps is not empty to avoid downstream crashes
        if not detected_dps:
            detected_dps = {"1": -1}

        # Merge cloud function DP IDs (from API) into detected list.
        # This ensures multi-channel devices (e.g., switch_1..switch_4) are not truncated.
        if cloud_dp_codes:
            _LOGGER.info(
                "[CL-DEBUG] Merging %s cloud DPs into detected list",
                len(cloud_dp_codes),
            )
            for cloud_dp in cloud_dp_codes:
                dp_id = str(cloud_dp)
                if dp_id not in detected_dps:
                    detected_dps[dp_id] = -1

        # Explicit discovery summary
        local_count = len([k for k, v in detected_dps.items() if v != -1])
        cloud_count = len([k for k, v in detected_dps.items() if v == -1])
        _LOGGER.info(
            "[CL-DEBUG] DISCOVERY SUMMARY: %s DPs found locally, %s DPs added from cloud. Total: %s",
            local_count,
            cloud_count,
            len(detected_dps),
        )
    
    logger.info("Total DPS detected: %s", detected_dps)
    
    # Cloud-first precedence: always merge cloud DP IDs in detected_dps before
    # building final labels so cloud metadata remains authoritative.
    if cloud_dp_codes:
        for cloud_dp in cloud_dp_codes:
            dp_id = str(cloud_dp)
            if dp_id not in detected_dps:
                detected_dps[dp_id] = -1

    # Final DP list used by the UI.
    # Cloud metadata has precedence; local values are fallback only.
    final_dps = dps_string_list(detected_dps, cloud_dp_codes)

    return {
        CONF_DPS_STRINGS: final_dps,
        CONF_PROTOCOL_VERSION: conf_protocol,
    }


async def attempt_cloud_connection(user_input):
    """Create device."""
    cloud_api = TuyaCloudApi(
        user_input.get(CONF_REGION),
        user_input.get(CONF_CLIENT_ID),
        user_input.get(CONF_CLIENT_SECRET),
        user_input.get(CONF_USER_ID),
    )

    msg, res = await cloud_api.async_connect()

    if res != "ok":
        return cloud_api, {"reason": msg, "msg": res}

    return cloud_api, {}
