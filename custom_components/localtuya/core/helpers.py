"""
Helpers functions for HASS-LocalTuya.
"""

import asyncio
import logging
import os.path
from enum import Enum
from fnmatch import fnmatch
from typing import NamedTuple

from homeassistant.util.yaml import load_yaml, dump
from homeassistant.const import CONF_PLATFORM, CONF_ENTITIES


import custom_components.localtuya.templates as templates_dir

JSON_TYPE = list | dict | str

_LOGGER = logging.getLogger(__name__)


###############################
#          Templates          #
###############################
class templates:

    def yaml_dump(config, fname: str | None = None) -> JSON_TYPE:
        """Save yaml config."""
        try:
            with open(fname, "w", encoding="utf-8") as conf_file:
                return conf_file.write(dump(config))
        except UnicodeDecodeError as exc:
            _LOGGER.error("Unable to save file %s: %s", fname, exc)

    def list_templates():
        """Return the available templates files."""
        dir = os.path.dirname(templates_dir.__file__)
        files = {}
        for e in sorted(os.scandir(dir), key=lambda e: e.name):
            file: str = e.name.lower()
            if e.is_file() and (fnmatch(file, "*yaml") or fnmatch(file, "*yml")):
                # fn = str(file).replace(".yaml", "").replace("_", " ")
                files[e.name] = e.name
        return files

    def import_config(filename):
        """Create a data that can be used as config in localtuya."""
        template_dir = os.path.dirname(templates_dir.__file__)
        template_file = os.path.join(template_dir, filename)
        _config = load_yaml(template_file)
        entities = []
        for cfg in _config:
            ent = {}
            for plat, values in cfg.items():
                for key, value in values.items():
                    ent[str(key)] = (
                        str(value)
                        if not isinstance(value, (bool, float, dict, list))
                        else value
                    )
                ent[CONF_PLATFORM] = plat
            entities.append(ent)
        if not entities:
            raise ValueError("No entities found the can be used for localtuya")
        return entities

    @classmethod
    def export_config(cls, config: dict, config_name: str):
        """Create a yaml config file for localtuya."""
        export_config = []
        for cfg in config[CONF_ENTITIES]:
            # Special case device_classes
            for k, v in cfg.items():
                if not type(v) is str and isinstance(v, Enum):
                    cfg[k] = v.value

            ents = {cfg[CONF_PLATFORM]: cfg}
            export_config.append(ents)
        fname = (
            config_name + ".yaml" if not config_name.endswith(".yaml") else config_name
        )
        fname = fname.replace(" ", "_")
        template_dir = os.path.dirname(templates_dir.__file__)
        template_file = os.path.join(template_dir, fname)

        cls.yaml_dump(export_config, template_file)


################################
##       config flows         ##
################################

from ..const import CONF_LOCAL_KEY, CONF_NODE_ID

GATEWAY = NamedTuple("Gateway", [("id", str), ("data", dict)])


def get_gateway_by_deviceid(device_id: str, cloud_data: dict) -> GATEWAY:
    """Return the gateway (id, data) of the sub-deviceID if existed in cloud_data."""

    if sub_device := cloud_data.get(device_id):
        for dev_id, dev_data in cloud_data.items():
            # Get gateway Assuming the LocalKey is the same gateway LocalKey!
            if (
                dev_id != device_id
                and not dev_data.get(CONF_NODE_ID)
                and dev_data.get(CONF_LOCAL_KEY) == sub_device.get(CONF_LOCAL_KEY)
            ):
                return GATEWAY(dev_id, dev_data)


###############################
#    Auto configure device    #
###############################
from .ha_entities import gen_localtuya_entities


def format_mac(mac: str | None) -> str | None:
    """Format MAC address with colons."""
    if not mac:
        return None
    clean = str(mac).lower().replace(":", "").replace("-", "").strip()
    if len(clean) == 12:
        return ":".join(clean[i:i + 2] for i in range(0, 12, 2))
    return mac


async def async_find_local_ip_by_mac(hass, mac: str) -> str | None:
    """Find local IP (192.168.0.x) for a given MAC address via ARP table and AdGuard DHCP."""
    if not mac:
        return None
    clean_target = str(mac).lower().replace(":", "").replace("-", "").strip()
    if not clean_target:
        return None

    # 1. Search in /proc/net/arp
    try:
        def _read_arp():
            try:
                with open("/proc/net/arp", "r", encoding="utf-8") as f:
                    for line in f.readlines()[1:]:
                        parts = line.split()
                        if len(parts) >= 4:
                            arp_ip = parts[0]
                            arp_mac = parts[3].lower().replace(":", "").replace("-", "").strip()
                            if arp_mac == clean_target and arp_ip.startswith("192.168.0."):
                                return arp_ip
            except Exception:
                pass
            return None

        arp_ip = await hass.async_add_executor_job(_read_arp)
        if arp_ip:
            _LOGGER.info("Found local IP %s in /proc/net/arp for MAC %s", arp_ip, mac)
            return arp_ip
    except Exception as err:
        _LOGGER.debug("Error checking /proc/net/arp for MAC %s: %s", mac, err)

    # 2. Search in AdGuard Home DHCP status
    try:
        # Default to the known direct IP — "homeassistant.local" does NOT resolve
        # inside the HA Docker container, so we always keep 192.168.0.3 as a fallback.
        ADGUARD_FALLBACK_IP = "192.168.0.3"
        adguard_hosts = [ADGUARD_FALLBACK_IP]
        adguard_port = 3001
        adguard_user = "carlo"
        adguard_pass = "casacp1!"

        for entry in hass.config_entries.async_entries("adguard"):
            if entry.data:
                entry_host = entry.data.get("host", ADGUARD_FALLBACK_IP)
                adguard_port = entry.data.get("port", adguard_port)
                adguard_user = entry.data.get("username", adguard_user)
                adguard_pass = entry.data.get("password", adguard_pass)
                # Prepend the entry hostname so it is tried first, then fall back to the
                # hardcoded IP in case the hostname doesn't resolve inside the container.
                if entry_host != ADGUARD_FALLBACK_IP:
                    adguard_hosts = [entry_host, ADGUARD_FALLBACK_IP]
                break

        import urllib.request
        import base64
        import json

        def _query_adguard():
            auth = base64.b64encode(f"{adguard_user}:{adguard_pass}".encode()).decode("ascii")
            for host in adguard_hosts:
                try:
                    url = f"http://{host}:{adguard_port}/control/dhcp/status"
                    req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        data = json.loads(resp.read().decode())
                        all_leases = data.get("leases", []) + data.get("static_leases", [])
                        for lease in all_leases:
                            lease_mac = str(lease.get("mac", "")).lower().replace(":", "").replace("-", "").strip()
                            if lease_mac == clean_target:
                                return lease.get("ip")
                    # Reached the end of leases list without a match — no need to retry other hosts
                    return None
                except Exception:
                    # This host failed (e.g. DNS resolution error) — try the next one
                    continue
            return None

        dhcp_ip = await hass.async_add_executor_job(_query_adguard)
        if dhcp_ip:
            _LOGGER.info("Found local IP %s in AdGuard DHCP for MAC %s", dhcp_ip, mac)
            return dhcp_ip
    except Exception as err:
        _LOGGER.debug("Error querying AdGuard DHCP for MAC %s: %s", mac, err)

    return None

