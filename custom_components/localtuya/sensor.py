"""Platform to present any Tuya DP as a sensor."""

import logging
import base64
from functools import partial
from .config_flow import col_to_select

import voluptuous as vol
from homeassistant.components.sensor import (
    DEVICE_CLASSES_SCHEMA,
    DOMAIN,
    STATE_CLASSES_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_DEVICES,
    CONF_HOST,
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
    Platform,
    STATE_UNKNOWN,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo

from .coordinator import HassLocalTuyaData
from .entity import LocalTuyaEntity
from .entity import async_setup_entry as _entity_async_setup_entry
from .const import CONF_NODE_ID, CONF_SCALING, CONF_OFFSET, CONF_STATE_CLASS
from .const import DOMAIN as LOCALTUYA_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_PRECISION = 2

ATTR_POWER = "power"
ATTR_VOLTAGE = "voltage"
ATTR_CURRENT = "current"
MAP_UOM = {
    ATTR_CURRENT: UnitOfElectricCurrent.AMPERE,
    ATTR_VOLTAGE: UnitOfElectricPotential.VOLT,
    ATTR_POWER: UnitOfPower.KILO_WATT,
}

# Default units for device classes when not explicitly configured
DEVICE_CLASS_DEFAULT_UNITS = {
    SensorDeviceClass.TEMPERATURE: UnitOfTemperature.CELSIUS,
    SensorDeviceClass.HUMIDITY: PERCENTAGE,
    SensorDeviceClass.PRESSURE: UnitOfPressure.HPA,
}


class LocalTuyaNetworkSensor(SensorEntity):
    """Diagnostic sensor exposing a device's local or cloud IP address.

    Home Assistant's device page only renders connections of type "mac",
    "bluetooth" and "zigbee" (see ha-device-info-card.ts _getAddresses());
    "ip" connections are stored in the registry but never shown. Exposing
    the address as a regular diagnostic entity instead makes it visible
    on the device page and usable in automations/templates/dashboards.
    """

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        dev_id: str,
        value_key: str,
        unique_key: str,
        name: str,
        icon: str,
    ) -> None:
        """Initialize the network diagnostic sensor."""
        self._entry = entry
        self._dev_id = dev_id
        self._value_key = value_key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"local_{dev_id}_{unique_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(LOCALTUYA_DOMAIN, f"local_{dev_id}")}
        )

    @property
    def native_value(self) -> str | None:
        """Return the current value read live from the config entry."""
        dev_conf = self._entry.data.get(CONF_DEVICES, {}).get(self._dev_id, {})
        return dev_conf.get(self._value_key) or None

    @property
    def available(self) -> bool:
        """Only show the entity while the underlying value is known."""
        return self.native_value is not None


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): str,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): col_to_select(
            [sc.value for sc in SensorStateClass]
        ),
        vol.Optional(CONF_SCALING): vol.All(
            vol.Coerce(float), vol.Range(min=-1000000.0, max=1000000.0)
        ),
        vol.Optional(CONF_OFFSET): vol.All(
            vol.Coerce(float), vol.Range(min=-1000000.0, max=1000000.0)
        ),
    }


class LocalTuyaSensor(LocalTuyaEntity, SensorEntity):
    """Representation of a Tuya sensor."""

    def __init__(
        self,
        device,
        config_entry,
        sensorid,
        **kwargs,
    ):
        """Initialize the Tuya sensor."""
        super().__init__(device, config_entry, sensorid, _LOGGER, **kwargs)
        self._state = None

        self._has_sub_entities = False
        self._attr_device_class = self._config.get(CONF_DEVICE_CLASS)

    @property
    def native_value(self):
        """Return sensor state."""
        return self._state

    @property
    def state_class(self) -> str | None:
        """Return state class."""
        return getattr(self, "_attr_state_class", self._config.get(CONF_STATE_CLASS))

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        # First check explicit attribute or config
        unit = getattr(
            self,
            "_attr_native_unit_of_measurement",
            self._config.get(CONF_UNIT_OF_MEASUREMENT),
        )
        # Treat empty string as None
        if unit == "":
            unit = None
        # Fall back to default unit for device class if not explicitly set
        if unit is None and self._attr_device_class:
            unit = DEVICE_CLASS_DEFAULT_UNITS.get(self._attr_device_class)
        return unit

    def status_updated(self):
        """Device status was updated."""

        state = self.dp_value(self._dp_id)

        if self.is_base64(state):
            if not self._has_sub_entities:
                self.hass.loop.call_soon_threadsafe(
                    self.hass.async_create_task, self.__create_sub_sensors()
                )

            if None not in (
                sub_sensor := getattr(self, "_attr_sub_sensor", None),
                sub_sensor_state := self.decode_base64(state).get(sub_sensor),
            ):
                self._state = sub_sensor_state
            else:
                self._state = state
        else:
            self._state = self.scale(state)

    def status_restored(self, stored_state) -> None:
        super().status_restored(stored_state)

        if (last_state := self._last_state) and self.is_base64(last_state):
            self._status.update({self._dp_id: last_state})

    # No need to restore state for a sensor
    async def restore_state_when_connected(self):
        """Do nothing for a sensor."""
        return

    def is_base64(self, data):
        """Return if the data is valid Tuya raw Base64 encoded data."""
        return (
            (data and isinstance(data, str))
            and len(data) >= 12
            and len(data) % 2 == 0
            and data.endswith("=")
        )

    def decode_base64(self, data):
        """Decode data base64 such as DPS phase_a."""
        buf = base64.b64decode(data)
        voltage = (buf[1] | buf[0] << 8) / 10
        current = (buf[4] | buf[3] << 8) / 1000
        power = (buf[7] | buf[6] << 8) / 1000
        return {ATTR_VOLTAGE: voltage, ATTR_CURRENT: current, ATTR_POWER: power}

    async def __create_sub_sensors(self):
        """Create sub entities for voltage, current and power and hide this parent sensor."""
        sub_entities = []

        for sensor in (ATTR_CURRENT, ATTR_POWER, ATTR_VOLTAGE):
            sub_entity = LocalTuyaSensor(
                self._device, self._device_config.as_dict(), self._dp_id
            )
            setattr(sub_entity, "_attr_sub_sensor", sensor)
            setattr(sub_entity, "_attr_unique_id", f"{self.unique_id}_{sensor}")
            setattr(sub_entity, "_attr_name", f"{self.name} {sensor.capitalize()}")
            setattr(sub_entity, "_attr_device_class", SensorDeviceClass(sensor))
            setattr(sub_entity, "_attr_state_class", SensorStateClass.MEASUREMENT)
            setattr(sub_entity, "_attr_native_unit_of_measurement", MAP_UOM[sensor])
            sub_entities.append(sub_entity)

        # Sub entities shouldn't have add entities attr.
        if sub_entities and self.component_add_entities:
            self._has_sub_entities = True
            self.component_add_entities(sub_entities)
            er.async_get(self.hass).async_update_entity(
                self.entity_id, hidden_by=er.RegistryEntryHider.INTEGRATION
            )


async def __create_sub_sensors(self):
        """Create sub entities for voltage, current and power and hide this parent sensor."""
        sub_entities = []

        for sensor in (ATTR_CURRENT, ATTR_POWER, ATTR_VOLTAGE):
            sub_entity = LocalTuyaSensor(
                self._device, self._device_config.as_dict(), self._dp_id
            )
            setattr(sub_entity, "_attr_sub_sensor", sensor)
            setattr(sub_entity, "_attr_unique_id", f"{self.unique_id}_{sensor}")
            setattr(sub_entity, "_attr_name", f"{self.name} {sensor.capitalize()}")
            setattr(sub_entity, "_attr_device_class", SensorDeviceClass(sensor))
            setattr(sub_entity, "_attr_state_class", SensorStateClass.MEASUREMENT)
            setattr(sub_entity, "_attr_native_unit_of_measurement", MAP_UOM[sensor])
            sub_entities.append(sub_entity)

        # Sub entities shouldn't have add entities attr.
        if sub_entities and self.component_add_entities:
            self._has_sub_entities = True
            self.component_add_entities(sub_entities)
            er.async_get(self.hass).async_update_entity(
                self.entity_id, hidden_by=er.RegistryEntryHider.INTEGRATION
            )


async def async_setup_entry(
    hass,
    config_entry: ConfigEntry,
    async_add_entities,
):
    """Set up LocalTuya sensors and diagnostic network sensors."""
    # First, run the original setup for regular DP sensors
    from .entity import async_setup_entry as _entity_async_setup_entry
    
    # Build the partial function manually with the first 3 args
    original_setup = partial(_entity_async_setup_entry, DOMAIN, LocalTuyaSensor, flow_schema)
    await original_setup(hass, config_entry, async_add_entities)

    # Then add diagnostic network sensors for each device that has IP info
    entry_data = config_entry.data
    devices = entry_data.get(CONF_DEVICES, {})
    network_entities = []

    for dev_id, dev_conf in devices.items():
        # Local IP (host)
        if dev_conf.get(CONF_HOST):
            network_entities.append(
                LocalTuyaNetworkSensor(
                    entry=config_entry,
                    dev_id=dev_id,
                    value_key=CONF_HOST,
                    unique_key="local_ip",
                    name="Local IP",
                    icon="mdi:ip-network",
                )
            )
        # Cloud IP
        if dev_conf.get("cloud_ip"):
            network_entities.append(
                LocalTuyaNetworkSensor(
                    entry=config_entry,
                    dev_id=dev_id,
                    value_key="cloud_ip",
                    unique_key="cloud_ip",
                    name="Cloud IP",
                    icon="mdi:cloud-outline",
                )
            )

    if network_entities:
        async_add_entities(network_entities)


# Export for HA's platform discovery
# Note: we don't use partial here because HA will call this function directly
# with the standard (hass, config_entry, async_add_entities) signature
