"""The LocalTuya integration."""

import asyncio
from dataclasses import dataclass
import logging
import time
from datetime import timedelta
from typing import Any, NamedTuple

import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DEVICES,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_FRIENDLY_NAME,
    CONF_HOST,
    CONF_ID,
    CONF_PLATFORM,
    CONF_REGION,
    EVENT_HOMEASSISTANT_STOP,
    SERVICE_RELOAD,
)
from homeassistant.core import Event, HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_time_interval

from .coordinator import TuyaDevice, HassLocalTuyaData, TuyaCloudApi
from .config_flow import ENTRIES_VERSION
from .const import (
    ATTR_UPDATED_AT,
    CONF_CLOUD_POLLING_ENABLED,
    CONF_DEVICE_SLEEP_TIME,
    CONF_DOWNLOAD_CLOUD_INFO,
    CONF_GATEWAY_ID,
    CONF_MAC_RETRIEVAL,
    CONF_MODEL,
    CONF_NODE_ID,
    CONF_NO_CLOUD,
    CONF_PRODUCT_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_STARTUP_CLOUD_POLL,
    CONF_USER_ID,
    DATA_DISCOVERY,
    DOMAIN,
    PLATFORMS,
)
from .network_manager import async_setup_network_manager
from .event_processor import async_setup_event_processor

from .discovery import TuyaDiscovery

_LOGGER = logging.getLogger(__name__)

# The integration is configured via config entries (UI). No YAML configuration.
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

CONF_DP = "dp"
CONF_VALUE = "value"

SERVICE_SET_DP = "set_dp"
SERVICE_SET_DP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_DP): int,
        vol.Required(CONF_VALUE): object,
    }
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the LocalTuya integration component."""
    hass.data.setdefault(DOMAIN, {})

    current_entries = hass.config_entries.async_entries(DOMAIN)
    device_cache = {}

    async def _handle_reload(service: ServiceCall):
        """Handle reload service call."""
        _LOGGER.info("Service %s.reload called: reloading integration", DOMAIN)

        current_entries = hass.config_entries.async_entries(DOMAIN)

        reload_tasks = [
            hass.config_entries.async_reload(entry.entry_id)
            for entry in current_entries
        ]
        await asyncio.gather(*reload_tasks)

    async def _handle_set_dp(event: ServiceCall):
        """Handle set_dp service call."""
        dev_id = event.data[CONF_DEVICE_ID]
        entry: ConfigEntry = async_config_entry_by_device_id(hass, dev_id)
        if not entry or not entry.entry_id:
            raise HomeAssistantError("unknown device id")

        host = entry.data[CONF_DEVICES][dev_id].get(CONF_HOST)
        if node_id := entry.data[CONF_DEVICES][dev_id].get(CONF_NODE_ID):
            host = f"{host}_{node_id}"
        device: TuyaDevice = hass.data[DOMAIN][entry.entry_id].devices[host]
        if not device.connected:
            raise HomeAssistantError("not connected to device")
        value = event.data[CONF_VALUE]
        if isinstance(value, dict):
            await device.set_dps(value)
        else:
            await device.set_dp(value, event.data[CONF_DP])

    def _device_discovered(device: dict):
        """Update address of device if it has changed."""
        device_ip = device["ip"]
        device_id = device["gwId"]
        product_key = device["productKey"]
        # If device is not in cache, check if a config entry exists
        entry: ConfigEntry = async_config_entry_by_device_id(hass, device_id)

        if entry is None:
            return

        hass_data: HassLocalTuyaData = hass.data[DOMAIN][entry.entry_id]

        if device_id not in device_cache or device_id not in device_cache.get(
            device_id, {}
        ):
            if entry and device_id in entry.data[CONF_DEVICES]:
                # Save address from config entry in cache to trigger
                # potential update below
                host_ip = entry.data[CONF_DEVICES][device_id][CONF_HOST]
                device_cache[device_id] = {device_id: host_ip}

        for subdev_id, dev_config in entry.data[CONF_DEVICES].items():
            if dev_config.get(CONF_NODE_ID):
                if gateway_id := dev_config.get(CONF_GATEWAY_ID):
                    if entry and device_id == gateway_id:
                        device_cache[device_id] = device_cache.get(device_id, {})
                        device_cache[device_id].update(
                            {subdev_id: dev_config.get(CONF_HOST)}
                        )

        if device_id not in device_cache:
            return
        if not entry.state == ConfigEntryState.LOADED:
            return

        if device := hass_data.devices.get(device_ip):
            ...

        # hass.create_task(hass_data.cloud_data.async_get_devices_list())
        new_data = entry.data.copy()
        updated = False
        pending_device_activated = False  # Track if a pending-discovery device got its IP
        for dev_id, host in device_cache[device_id].items():
            if dev_id not in entry.data[CONF_DEVICES]:
                continue
            dev_entry = entry.data[CONF_DEVICES][dev_id]
            if host != device_ip:
                updated = True
                new_data[CONF_DEVICES][dev_id][CONF_HOST] = device_ip
                device_cache[device_id][dev_id] = device_ip

                # If device was registered with placeholder IP, clear the flag
                if dev_entry.get("pending_discovery") and host == "0.0.0.0":
                    new_data[CONF_DEVICES][dev_id].pop("pending_discovery", None)
                    pending_device_activated = True
                    _LOGGER.info(
                        "[SLEEPY-DEVICE] Device %s woke up! Real IP resolved: %s → %s. "
                        "Reloading config entry to connect.",
                        dev_id, host, device_ip,
                    )

            if (p_key := dev_entry.get(CONF_PRODUCT_KEY)) and p_key != product_key:
                updated = True
                new_data[CONF_DEVICES][dev_id][CONF_PRODUCT_KEY] = product_key
        # Update settings if something changed, otherwise try to connect. Updating
        # settings triggers a reload of the config entry, which tears down the device
        # so no need to connect in that case.
        if updated:
            _LOGGER.debug(
                "Updating keys for device %s: %s %s", device_id, device_ip, product_key
            )
            new_data[ATTR_UPDATED_AT] = str(int(time.time() * 1000))
            hass.config_entries.async_update_entry(entry, data=new_data)
            # Force a reload if a previously-sleeping device just got its real IP
            if pending_device_activated:
                hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

    def _shutdown(event):
        """Clean up resources when shutting down."""
        discovery.close()

    hass.services.async_register(DOMAIN, SERVICE_RELOAD, _handle_reload)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_DP, _handle_set_dp, schema=SERVICE_SET_DP_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, "refresh_mac", _handle_refresh_mac,
        schema=vol.Schema({
            vol.Required(CONF_DEVICE_ID): cv.string,
        })
    )

    discovery = TuyaDiscovery(_device_discovered)
    try:
        await discovery.start()
        hass.data[DOMAIN][DATA_DISCOVERY] = discovery
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _shutdown)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("failed to set up discovery")

    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entries merging all of them in one."""
    new_version = ENTRIES_VERSION
    stored_entries = hass.config_entries.async_entries(DOMAIN)
    if config_entry.version == 1:
        # This an old version of original integration no need to put it here.
        pass
    # Update to version 3
    if config_entry.version == 2:
        # Switch config flow to selectors convert DP IDs from int to str require HA 2022.4.
        _LOGGER.debug("Migrating config entry from version %s", config_entry.version)
        new_data = config_entry.data.copy()
        for device in new_data[CONF_DEVICES]:
            i = 0
            for _ent in new_data[CONF_DEVICES][device][CONF_ENTITIES]:
                ent_items = {}
                for k, v in _ent.items():
                    ent_items[k] = str(v) if type(v) is int else v
                new_data[CONF_DEVICES][device][CONF_ENTITIES][i].update(ent_items)
                i = i + 1
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=3)
    # Update to version 4
    if config_entry.version <= 3:
        # Convert values and friendly name values to dict.
        from .const import (
            Platform,
            CONF_OPTIONS,
            CONF_HVAC_MODE_SET,
            CONF_HVAC_ACTION_SET,
            CONF_PRESET_SET,
            CONF_SCENE_VALUES,
            # Deprecated
            CONF_SCENE_VALUES_FRIENDLY,
            CONF_OPTIONS_FRIENDLY,
            CONF_HVAC_ADD_OFF,
        )
        from .climate import (
            RENAME_HVAC_MODE_SETS,
            RENAME_ACTION_SETS,
            RENAME_PRESET_SETS,
            HVAC_OFF,
        )

        def convert_str_to_dict(list1: str, list2: str = ""):
            to_dict = {}
            if not isinstance(list1, str):
                return list1
            list1, list2 = list1.replace(";", ","), list2.replace(";", ",")
            v, v_fn = list1.split(","), list2.split(",")
            for k in range(len(v)):
                to_dict[v[k]] = (
                    v_fn[k] if k < len(v_fn) and v_fn[k] else v[k].capitalize()
                )
            return to_dict

        new_data = config_entry.data.copy()
        for device in new_data[CONF_DEVICES]:
            current_entity = 0
            for entity in new_data[CONF_DEVICES][device][CONF_ENTITIES]:
                new_entity_data = {}
                if entity[CONF_PLATFORM] == Platform.SELECT:
                    # Merge 2 Lists Values and Values friendly names into dict.
                    v_fn = entity.get(CONF_OPTIONS_FRIENDLY, "")
                    if v := entity.get(CONF_OPTIONS):
                        new_entity_data[CONF_OPTIONS] = convert_str_to_dict(v, v_fn)
                if entity[CONF_PLATFORM] == Platform.LIGHT:
                    v_fn = entity.get(CONF_SCENE_VALUES_FRIENDLY, "")
                    if v := entity.get(CONF_SCENE_VALUES):
                        new_entity_data[CONF_SCENE_VALUES] = convert_str_to_dict(
                            v, v_fn
                        )
                if entity[CONF_PLATFORM] == Platform.CLIMATE:
                    # Merge 2 Lists Values and Values friendly names into dict.
                    climate_to_dict = {}
                    for conf, new_values in (
                        (CONF_HVAC_MODE_SET, RENAME_HVAC_MODE_SETS),
                        (CONF_HVAC_ACTION_SET, RENAME_ACTION_SETS),
                        (CONF_PRESET_SET, RENAME_PRESET_SETS),
                    ):
                        climate_to_dict[conf] = {}
                        if hvac_set := entity.get(conf, ""):
                            if entity.get(CONF_HVAC_ADD_OFF, False):
                                if conf == CONF_HVAC_MODE_SET:
                                    climate_to_dict[conf].update(HVAC_OFF)
                            if not isinstance(conf, str):
                                continue
                            hvac_set = hvac_set.replace("/", ",")
                            for i in hvac_set.split(","):
                                for k, v in new_values.items():
                                    if i in k:
                                        new_v = True if i == "True" else i
                                        new_v = False if i == "False" else new_v
                                        climate_to_dict[conf].update({v: new_v})
                    new_entity_data = climate_to_dict
                new_data[CONF_DEVICES][device][CONF_ENTITIES][current_entity].update(
                    new_entity_data
                )
                current_entity += 1
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=4)

    _LOGGER.info(
        "Entry %s successfully migrated to version %s.",
        config_entry.entry_id,
        new_version,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up LocalTuya integration from a config entry."""
    if entry.version < ENTRIES_VERSION:
        _LOGGER.debug(
            "Skipping setup for entry %s since its version (%s) is old",
            entry.entry_id,
            entry.version,
        )
        return

    region = entry.data[CONF_REGION]
    client_id = entry.data[CONF_CLIENT_ID]
    secret = entry.data[CONF_CLIENT_SECRET]
    user_id = entry.data[CONF_USER_ID]
    tuya_api = TuyaCloudApi(region, client_id, secret, user_id)
    no_cloud = entry.data.get(CONF_NO_CLOUD, True)

    if no_cloud:
        _LOGGER.info(f"Cloud API account not configured.")
    else:
        entry.async_create_background_task(
            hass, tuya_api.async_connect(), "localtuya-cloudAPI"
        )

    hass_localtuya = HassLocalTuyaData(tuya_api, {})
    hass.data[DOMAIN][entry.entry_id] = hass_localtuya

    def _setup_devices(entry_devices: dict):
        """Setup Localtuya devices object."""
        devices = hass_localtuya.devices
        connect_to_devices: list[TuyaDevice] = []

        # Sort parent devices first then sub-devices.
        sorted_devices = dict(
            sorted(
                entry_devices.items(), key=lambda k: 1 if k[1].get(CONF_NODE_ID) else 0
            )
        )

        for dev_id, config in sorted_devices.items():
            if check_if_device_disabled(hass, entry, dev_id):
                continue

            host = config.get(CONF_HOST)

            # Skip local connection for cloud-only devices (sleepy devices or placeholder IP)
            is_cloud_only = (
                config.get(CONF_DEVICE_SLEEP_TIME, 0) > 0 
                or config.get(CONF_HOST) == "0.0.0.0"
            )
            if is_cloud_only:
                _LOGGER.info(
                    "Device %s is cloud-only (sleep_time > 0 or placeholder IP) — skipping local connection",
                    dev_id
                )
                # Still create device object for entity setup but don't connect locally
                if not (node_id := config.get(CONF_NODE_ID)):
                    devices[config.get(CONF_HOST, dev_id)] = TuyaDevice(hass, entry, config)
                continue

            host = config.get(CONF_HOST)

            # Parent Devices.
            if not (node_id := config.get(CONF_NODE_ID)):
                devices[host] = (dev := TuyaDevice(hass, entry, config))
                connect_to_devices.append(dev)
                continue

            # Sub-Devices
            if not (gateway := devices.get(host)):
                # Setup sub-device as fake gateway if there is no a gateway exist.
                devices[host] = (gateway := TuyaDevice(hass, entry, config, True))
                connect_to_devices.append(gateway)

            devices[f"{host}_{node_id}"] = (sub_dev := TuyaDevice(hass, entry, config))
            sub_dev.gateway = gateway
            gateway.sub_devices[node_id] = sub_dev

        return connect_to_devices

    connect_to_devices = _setup_devices(entry.data[CONF_DEVICES])

    # Ensure all devices in config entry are registered in HA DeviceRegistry immediately with their friendly names
    device_registry = dr.async_get(hass)

    # First, collect all current IPs from config to detect stale device registry entries
    current_ips = {}
    for dev_id, dev_config in entry.data[CONF_DEVICES].items():
        if (host := dev_config.get(CONF_HOST)) and host != "0.0.0.0":
            current_ips[host] = dev_id

    # Remove stale IP connections from device registry (IPs that belong to different devices in config)
    for dev_id, dev_config in entry.data[CONF_DEVICES].items():
        if (host := dev_config.get(CONF_HOST)) and host != "0.0.0.0":
            # Check if this IP is registered to a different device in the registry
            existing_device = None
            for device_entry in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
                for conn_type, conn_value in device_entry.connections:
                    if conn_type == "ip" and conn_value == host:
                        # Check if this device has the correct identifier
                        has_correct_id = any(
                            id_type == DOMAIN and id_value == f"local_{dev_id}"
                            for id_type, id_value in device_entry.identifiers
                        )
                        if not has_correct_id:
                            existing_device = device_entry
                            break
                if existing_device:
                    break

            if existing_device:
                _LOGGER.warning(
                    "Removing stale IP connection %s from device %s (belongs to %s in config)",
                    host,
                    existing_device.name,
                    dev_id,
                )
                # Remove the stale IP connection
                new_connections = {
                    (conn_type, conn_value)
                    for conn_type, conn_value in existing_device.connections
                    if not (conn_type == "ip" and conn_value == host)
                }
                device_registry.async_update_device(
                    existing_device.id,
                    new_connections=new_connections if new_connections else None,
                )

    # Now register/update devices with current config
    for dev_id, dev_config in entry.data[CONF_DEVICES].items():
        dev_name = (
            dev_config.get(CONF_FRIENDLY_NAME)
            or dev_config.get("name")
            or dev_config.get("cloud_name")
            or f"Tuya {dev_id}"
        )
        model_str = f"{dev_config.get(CONF_MODEL, 'Tuya generic')} ({dev_id})"
        if cloud_prod := dev_config.get("cloud_product_name"):
            model_str = f"{model_str} - {cloud_prod}"

        connections = set()
        if mac := (dev_config.get("mac") or dev_config.get("cloud_mac")):
            connections.add(("mac", mac))
        if (host := dev_config.get(CONF_HOST)) and host != "0.0.0.0":
            connections.add(("ip", host))

        via_device_id = None
        if gateway_id := dev_config.get(CONF_GATEWAY_ID):
            via_device_id = (DOMAIN, f"local_{gateway_id}")

        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"local_{dev_id}")},
            name=dev_name,
            manufacturer="Tuya",
            model=model_str,
            sw_version=str(dev_config.get(CONF_PROTOCOL_VERSION, "auto")),
            configuration_url=f"http://{host}" if host and host != "0.0.0.0" else None,
            via_device_id=via_device_id,
            connections=connections if connections else None,
        )

    await async_remove_orphan_entities(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS.values())

    # Note: entry.async_on_unload items are called in LIFO order!

    for dev in connect_to_devices:
        entry.async_create_task(hass, dev.async_connect())
        entry.async_on_unload(dev.close)

    # Initialize network manager for cloud-only devices
    network_manager = await async_setup_network_manager(hass, hass.data[DOMAIN][entry.entry_id], entry)
    entry.async_on_unload(network_manager.async_stop)

    # Initialize event processor for cloud-only device cloud polling
    from .event_processor import async_setup_event_processor
    event_processor = await async_setup_event_processor(hass, hass.data[DOMAIN][entry.entry_id], entry)
    # Release the event bus listener on unload, otherwise every reload leaves
    # a live listener behind and each network event gets polled N times.
    entry.async_on_unload(event_processor.async_stop)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Initial cloud info download if enabled
    if entry.data.get(CONF_DOWNLOAD_CLOUD_INFO, False):
        entry.async_create_task(hass, _download_cloud_info_on_startup(hass, entry))

    # Initial cloud state polling for cloud-only devices
    if entry.data.get(CONF_STARTUP_CLOUD_POLL, True):
        entry.async_create_task(hass, _poll_cloud_devices_on_startup(hass, entry))

    async def _shutdown(event):
        """Clean up resources when shutting down."""
        await asyncio.gather(*[dev.close() for dev in connect_to_devices])
        _LOGGER.info(f"{entry.title}: Shutdown completed")

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _shutdown)
    )

    entry.async_on_unload(_run_async_listen(hass, entry))
    _LOGGER.info(f"{entry.title}: Setup completed")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unloading the Tuya platforms."""
    # Unload the platforms.
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS.values())
    hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.info("Unload completed")
    return True


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update listener: triggered whenever config entry data changes."""
    _LOGGER.info("LocalTuya config entry updated for %s: reloading integration entry", config_entry.entry_id)
    await hass.config_entries.async_reload(config_entry.entry_id)


async def _download_cloud_info_on_startup(hass: HomeAssistant, entry: ConfigEntry):
    """Download MAC addresses on startup if enabled (one device at a time)."""
    hass_data = hass.data[DOMAIN].get(entry.entry_id)
    if not hass_data or not hass_data.cloud_data:
        return
    
    try:
        _LOGGER.info("Downloading MAC addresses on startup (one device at a time)...")
        device_ids = list(entry.data.get(CONF_DEVICES, {}).keys())
        if not device_ids:
            return
        
        new_data = entry.data.copy()
        updated = False
        
        # Call factory info API one device at a time (like Tuya GUI does)
        for device_id in device_ids:
            try:
                factory_info = await hass_data.cloud_data.async_get_device_factory_info(device_id)
                
                if factory_info and "result" in factory_info and factory_info["result"]:
                    for device_info in factory_info["result"]:
                        dev_id = device_info.get("id") or device_info.get("device_id")
                        mac = device_info.get("mac")
                        sn = device_info.get("sn")
                        uuid = device_info.get("uuid")
                        if dev_id and mac and mac != "00:00:00:00:00:00" and dev_id in new_data.get(CONF_DEVICES, {}):
                            new_data[CONF_DEVICES][dev_id][CONF_MAC] = mac
                            if sn:
                                new_data[CONF_DEVICES][dev_id]["cloud_sn"] = sn
                            if uuid:
                                new_data[CONF_DEVICES][dev_id]["cloud_uuid"] = uuid
                            updated = True
                            _LOGGER.info(f"MAC address retrieved for {dev_id}: {mac}")
            except Exception as e:
                if "1106" in str(e) or "permission deny" in str(e).lower():
                    _LOGGER.info(f"MAC retrieval for {device_id} skipped - API permission required in Tuya IoT platform (enable 'Device Factory Info' API in project settings)")
                else:
                    _LOGGER.warning(f"Failed to get factory info for {device_id}: {e}")
        
        if updated:
            new_data[ATTR_UPDATED_AT] = str(int(time.time() * 1000))
            hass.config_entries.async_update_entry(entry, data=new_data)
            _LOGGER.info("MAC addresses downloaded and updated for all devices on startup")
        else:
            _LOGGER.info("No MAC address updates were applied on startup (API may require additional permissions in Tuya IoT platform)")
    except Exception as e:
        if "1106" in str(e) or "permission deny" in str(e).lower():
            _LOGGER.info("MAC retrieval skipped - API permission required in Tuya IoT platform (enable 'Device Factory Info' API in project settings)")
        else:
            _LOGGER.warning(f"Failed to download MAC addresses on startup: {e}")


async def _poll_cloud_devices_on_startup(hass: HomeAssistant, entry: ConfigEntry):
    """Query Tuya Cloud for current state of cloud-only devices on startup.
    
    Cloud-only devices (sleepy devices with device_sleep_time > 0 or placeholder IP 0.0.0.0)
    need a cloud handshake to enable their local port. This function proactively queries
    the cloud for their latest state so entities are available immediately after HA startup.
    """
    hass_data = hass.data[DOMAIN].get(entry.entry_id)
    if not hass_data or not hass_data.cloud_data:
        _LOGGER.debug("Cloud data not available, skipping startup cloud poll")
        return
    
    if entry.data.get(CONF_NO_CLOUD, True):
        _LOGGER.debug("Cloud not configured, skipping startup cloud poll")
        return

    try:
        _LOGGER.info("Polling Tuya Cloud for cloud-only device states on startup...")
        
        # Find all cloud-only devices
        cloud_only_devices = []
        for device_id, dev_config in entry.data.get(CONF_DEVICES, {}).items():
            is_cloud_only = (
                dev_config.get(CONF_DEVICE_SLEEP_TIME, 0) > 0 
                or dev_config.get(CONF_HOST) == "0.0.0.0"
            )
            # Also check if cloud polling is enabled for this device
            if is_cloud_only and dev_config.get(CONF_CLOUD_POLLING_ENABLED, True):
                cloud_only_devices.append(device_id)
        
        if not cloud_only_devices:
            _LOGGER.debug("No cloud-only devices with cloud polling enabled found")
            return
        
        _LOGGER.info(f"Found {len(cloud_only_devices)} cloud-only device(s) to poll: {', '.join(cloud_only_devices)}")
        
        # Query each device from cloud
        for device_id in cloud_only_devices:
            try:
                # Check if device exists in local coordinator
                device = None
                for key, dev in hass_data.devices.items():
                    if dev._device_config.id == device_id:
                        device = dev
                        break
                
                if device:
                    _LOGGER.info(f"Querying cloud state for cloud-only device: {device_id}")
                    # Use the device's method to poll cloud and update status
                    await device.async_update_from_cloud(device_id)
                else:
                    _LOGGER.debug(f"Device {device_id} not yet in coordinator, skipping cloud poll")
                    
            except Exception as e:
                _LOGGER.warning(f"Failed to poll cloud state for {device_id} on startup: {e}")
                
        _LOGGER.info("Startup cloud polling completed for cloud-only devices")
        
    except Exception as e:
        _LOGGER.warning(f"Failed to poll cloud devices on startup: {e}")


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    dev_id = _device_id_by_identifiers(device_entry.identifiers)

    ent_reg = er.async_get(hass)
    entities = {
        ent.unique_id: ent.entity_id
        for ent in er.async_entries_for_config_entry(ent_reg, config_entry.entry_id)
        if dev_id in ent.unique_id
    }
    for entity_id in entities.values():
        ent_reg.async_remove(entity_id)

    if dev_id not in config_entry.data[CONF_DEVICES]:
        _LOGGER.info(
            "Device %s not found in config entry: finalizing device removal", dev_id
        )
        return True

    # host = config_entry.data[CONF_DEVICES][dev_id][CONF_HOST]
    # await hass.data[DOMAIN][config_entry.entry_id].devices[host].close()

    new_data = config_entry.data.copy()
    new_data[CONF_DEVICES].pop(dev_id)
    new_data[ATTR_UPDATED_AT] = str(int(time.time() * 1000))

    hass.config_entries.async_update_entry(
        config_entry,
        data=new_data,
    )

    _LOGGER.info("Device %s removed.", dev_id)

    return True


async def async_remove_orphan_entities(hass, entry):
    """Remove entities associated with config entry that has been removed."""
    return
    ent_reg = er.async_get(hass)
    entities = {
        ent.unique_id: ent.entity_id
        for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    }
    _LOGGER.info("ENTITIES ORPHAN %s", entities)
    return

    for entity in entry.data[CONF_ENTITIES]:
        if entity[CONF_ID] in entities:
            del entities[entity[CONF_ID]]

    for entity_id in entities.values():
        ent_reg.async_remove(entity_id)


def _run_async_listen(hass: HomeAssistant, entry: ConfigEntry):
    """Start the listing events"""

    @callback
    def _event_filter(data: dr.EventDeviceRegistryUpdatedData) -> bool:
        device_reg = dr.async_get(hass).async_get(data["device_id"])
        is_entry = device_reg and entry.entry_id in device_reg.config_entries
        return data["action"] == "update" and is_entry

    async def device_state_changed(event: Event[dr.EventDeviceRegistryUpdatedData]):
        """Close connection if device disabled."""
        if not "disabled_by" in event.data["changes"]:
            return

        device_registry = dr.async_get(hass).async_get(event.data["device_id"])

        if not device_registry.disabled:
            return

        hass_localtuya: HassLocalTuyaData = hass.data[DOMAIN][entry.entry_id]

        dev_id = _device_id_by_identifiers(device_registry.identifiers)
        host_ip = entry.data[CONF_DEVICES][dev_id][CONF_HOST]

        if cid := entry.data[CONF_DEVICES][dev_id].get(CONF_NODE_ID):
            host_ip = f"{host_ip}_{cid}"

        device = hass_localtuya.devices.get(host_ip)

        if device:
            # If this is a gateway or fake gateway then reload entry to start using another device as GW.
            if device.sub_devices or (device.gateway and device.gateway.id == dev_id):
                await hass.config_entries.async_reload(entry.entry_id)
            else:
                await device.close()

    return hass.bus.async_listen(
        dr.EVENT_DEVICE_REGISTRY_UPDATED, device_state_changed, _event_filter
    )


async def _handle_refresh_mac(call: ServiceCall) -> None:
    """Handle the refresh_mac service call to manually trigger MAC address retrieval."""
    device_id = call.data[CONF_DEVICE_ID]
    _LOGGER.debug("Manual MAC refresh requested for device %s", device_id)

    # Find the config entry for this device
    entry = async_config_entry_by_device_id(hass, device_id)
    if not entry:
        _LOGGER.error("Device %s not found in any LocalTuya config entry", device_id)
        raise HomeAssistantError(f"Device {device_id} not found in LocalTuya integration")

    # Get the coordinator data
    hass_data = hass.data[DOMAIN].get(entry.entry_id)
    if not hass_data:
        _LOGGER.error("LocalTuya data not found for entry %s", entry.entry_id)
        raise HomeAssistantError(f"LocalTuya data not found for entry {entry.entry_id}")

    # Get the device config
    device_config = entry.data.get(CONF_DEVICES, {}).get(device_id)
    if not device_config:
        _LOGGER.error("Device %s not found in config entry %s", device_id, entry.entry_id)
        raise HomeAssistantError(f"Device {device_id} not found in config entry {entry.entry_id}")

    # Check if MAC retrieval is enabled at config entry level
    if not entry.data.get(CONF_MAC_RETRIEVAL, False):
        _LOGGER.warning("MAC retrieval not enabled in LocalTuya configuration")
        raise HomeAssistantError("MAC retrieval not enabled. Enable 'Retrieve MAC address from Tuya Cloud' in LocalTuya cloud configuration.")

    # Get the device from hass_data
    host = device_config.get(CONF_HOST)
    if not host:
        _LOGGER.error("Device %s has no host configured", device_id)
        raise HomeAssistantError(f"Device {device_id} has no host configured")

    # Find the device in the coordinator
    device = None
    for key, dev in hass.data[DOMAIN][entry.entry_id].devices.items():
        if dev._device_config.id == device_id:
            device = dev
            break

    if not device:
        _LOGGER.error("Device %s not found in coordinator", device_id)
        raise HomeAssistantError(f"Device {device_id} not found in coordinator")

    # Trigger MAC retrieval
    _LOGGER.info("Manual MAC address retrieval triggered for device %s", device_id)
    await device._retrieve_mac_address(device._device_config.id)

    # Reload the config entry to refresh the UI
    await hass.config_entries.async_reload(entry.entry_id)


def _device_id_by_identifiers(identifiers: set[tuple[str, str]]):
    """Return localtuya device ID by device registry identifiers."""
    return list(identifiers)[0][1].split("_")[-1]


@callback
def async_config_entry_by_device_id(hass: HomeAssistant, device_id: str):
    """Look up config entry by device id."""
    current_entries = hass.config_entries.async_entries(DOMAIN)
    for entry in current_entries:
        if device_id in entry.data[CONF_DEVICES]:
            return entry
        # Search for gateway_id
        for dev_conf in entry.data[CONF_DEVICES].values():
            if (gw_id := dev_conf.get(CONF_GATEWAY_ID)) and gw_id == device_id:
                return entry
    return None


@callback
def async_device_id_by_entity_id(hass: HomeAssistant, entity_id: str):
    """Look up config entry by device id."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    if device := dev_reg.async_get(ent_reg.async_get(entity_id).device_id):
        return list(device.identifiers)[0][1].split("_")[-1]

    return None


@callback
def check_if_device_disabled(hass: HomeAssistant, entry: ConfigEntry, dev_id: str):
    """Return whether if the device disabled or not."""
    ent_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
    ha_device_id: str = None

    for entity in entries:
        if dev_id in entity.unique_id:
            ha_device_id = entity.device_id
            break

    if ha_device_id and (device := dr.async_get(hass).async_get(ha_device_id)):
        return device.disabled
