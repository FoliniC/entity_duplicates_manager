from flask import Flask, render_template_string, jsonify, request
import sys
import os
import asyncio
import json
import logging
import time
from pathlib import Path
from threading import Thread
import subprocess

# v1.2.5 - Fix space management button enabling + logging enhancements
# v1.2.4 - Space management API + frontend
# v1.2.1 - Refresh stale local_key from Tuya Cloud at runtime and classify
#          session-key negotiation failures explicitly.
VERSION = "1.2.5"

# ---------------------------------------------------------------------------
# Library path – prioritise the local localtuya/core over any system package
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CORE_PATH = BASE_DIR / "custom_components" / "localtuya" / "core"
LOCALTUYA_CORE_PATH = Path(
    os.environ.get("LOCALTUYA_CORE_PATH", str(DEFAULT_CORE_PATH))
).expanduser()

if str(LOCALTUYA_CORE_PATH) not in sys.path:
    sys.path.insert(0, str(LOCALTUYA_CORE_PATH))
try:
    from pytuya import connect, TuyaListener
    from cloud_api import TuyaCloudApi
except ImportError as e:
    connect = None
    TuyaCloudApi = None
    TuyaListener = object
    import traceback
    print("Dependencies not found. Traceback follows:")
    traceback.print_exc()
    print("Set LOCALTUYA_CORE_PATH to localtuya/core path.")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Reduce werkzeug access logs (HTTP request logging)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# Add file logging with rotation
from logging.handlers import RotatingFileHandler
log_dir = BASE_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "tuya_gui.log"

file_handler = RotatingFileHandler(
    log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
))

# Get root logger and add file handler
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)

_log = logging.getLogger("tuya_gui")
_log.info("=== tuya_gui %s starting ===", VERSION)
_log.info("connect=%s  TuyaCloudApi=%s", connect, TuyaCloudApi)
_log.info("Log file: %s", log_file)

def _filter_numeric_dps(dps_dict: dict) -> dict:
    """Restituisce un dict contenente solo chiavi numeriche (int o stringhe di cifre)."""
    if not isinstance(dps_dict, dict):
        return {}
    filtered = {}
    for k, v in dps_dict.items():
        if isinstance(k, int):
            filtered[k] = v
        elif isinstance(k, str) and k.isdigit():
            filtered[int(k)] = v
    return filtered
    
app = Flask(__name__)
HA_CONFIG_BASE = Path(os.environ.get("HA_CONFIG_DIR", str(BASE_DIR))).expanduser()
CONFIG_PATH = Path(
    os.environ.get("HA_CORE_CONFIG_ENTRIES_PATH", str(HA_CONFIG_BASE / ".storage" / "core.config_entries"))
).expanduser()
ENTITY_REGISTRY_PATH = Path(
    os.environ.get("HA_ENTITY_REGISTRY_PATH", str(HA_CONFIG_BASE / ".storage" / "core.entity_registry"))
).expanduser()
RESTORE_STATE_PATH = Path(
    os.environ.get("HA_RESTORE_STATE_PATH", str(HA_CONFIG_BASE / ".storage" / "core.restore_state"))
).expanduser()
SETTINGS_PATH = Path(
    os.environ.get("TUYA_GUI_SETTINGS_PATH", str(HA_CONFIG_BASE / "tuya_manager_settings.json"))
).expanduser()

# ---------------------------------------------------------------------------
# Shared event loop running in a background thread
# ---------------------------------------------------------------------------
loop = asyncio.new_event_loop()

def start_loop(l: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(l)
    l.run_forever()

Thread(target=start_loop, args=(loop,), daemon=True).start()


# ---------------------------------------------------------------------------
# DeviceConnectionPool
# ---------------------------------------------------------------------------
class DeviceConnectionPool:
    """Maintains persistent, reusable TCP sessions to Tuya devices.

    Instead of opening and tearing down a connection on every status poll
    (which forces a full session-key re-negotiation each time — a primary
    source of CMDType.SESS_KEY_NEG_START failures on v3.4 devices), this pool
    keeps connections alive and reuses them across requests.

    A background ``heartbeat()`` coroutine periodically calls ``status()`` on
    every cached device to prevent the firmware from timing out the TCP socket
    due to inactivity.  Any connection that fails the heartbeat is evicted so
    the next caller transparently gets a fresh one.

    Usage (all calls must be awaited on the shared event loop):

        pool = DeviceConnectionPool()
        proto = await pool.get(dev_id, device_config_dict)
        result = await proto.status()
        # Do NOT close the transport — the pool manages the lifetime.
    """

    # Seconds between heartbeat sweeps (a status() is sent to every cached device)
    HEARTBEAT_INTERVAL: int = 20
    # If a connection has been idle longer than this it is proactively closed
    MAX_IDLE_SECONDS: int = 120
    # Per-connection status() timeout during heartbeat
    HEARTBEAT_TIMEOUT: int = 8

    def __init__(self) -> None:
        self._pool: dict[str, object] = {}        # dev_id -> protocol object
        self._last_used: dict[str, float] = {}    # dev_id -> loop.time()
        self._fingerprints: dict[str, tuple] = {}  # dev_id -> connection parameters
        # Serialises get/create so that concurrent requests for the same device
        # do not race to create two connections.
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get(self, dev_id: str, d: dict) -> object:
        """Return a live protocol connection for *dev_id*.

        Reuses an existing connection when it is still open; otherwise
        creates a new one.  Raises on connection failure so callers can
        catch and classify the exception.
        """
        async with self._lock:
            fingerprint = self._fingerprint(d)
            proto = self._pool.get(dev_id)
            if proto is not None:
                transport = getattr(proto, "transport", None)
                if (
                    transport is not None
                    and not transport.is_closing()
                    and self._fingerprints.get(dev_id) == fingerprint
                ):
                    self._last_used[dev_id] = loop.time()
                    return proto
                # Stale entry – close silently and reconnect
                self._close_proto(proto)
                self._pool.pop(dev_id, None)
                self._last_used.pop(dev_id, None)
                self._fingerprints.pop(dev_id, None)

            proto = await asyncio.wait_for(
                connect(
                    address=d["host"],
                    device_id=d["device_id"],
                    local_key=d["local_key"],
                    protocol_version=float(d.get("protocol_version", 3.3)),
                    enable_debug=True,
                    timeout=15,
                ),
                timeout=20,
            )
            self._pool[dev_id] = proto
            self._last_used[dev_id] = loop.time()
            self._fingerprints[dev_id] = fingerprint
            return proto

    def invalidate(self, dev_id: str) -> None:
        """Evict and close the cached connection for *dev_id*.

        Call this whenever a status/command call fails so the next request
        creates a fresh session rather than retrying on the same broken socket.
        """
        proto = self._pool.pop(dev_id, None)
        self._last_used.pop(dev_id, None)
        self._fingerprints.pop(dev_id, None)
        self._close_proto(proto)

    # ------------------------------------------------------------------
    # Heartbeat (long-running coroutine — scheduled once at startup)
    # ------------------------------------------------------------------

    async def heartbeat(self) -> None:
        """Keep cached connections alive with periodic status() polls.

        Evicts any connection that is idle beyond MAX_IDLE_SECONDS or fails
        the status call.  Logs at DEBUG/WARNING level so operators can see
        pool activity without noise in normal operation.
        """
        _log = logging.getLogger(__name__ + ".pool")
        while True:
            await asyncio.sleep(self.HEARTBEAT_INTERVAL)
            now = loop.time()
            for dev_id in list(self._pool.keys()):
                idle = now - self._last_used.get(dev_id, 0)
                if idle > self.MAX_IDLE_SECONDS:
                    _log.debug(
                        "Pool: evicting idle connection for %s (idle %.0fs)", dev_id, idle
                    )
                    self.invalidate(dev_id)
                    continue
                proto = self._pool.get(dev_id)
                if proto is None:
                    continue
                try:
                    await asyncio.wait_for(proto.status(), timeout=self.HEARTBEAT_TIMEOUT)
                    self._last_used[dev_id] = loop.time()
                    _log.debug("Pool: heartbeat OK for %s", dev_id)
                except Exception as exc:
                    _log.warning(
                        "Pool: heartbeat FAILED for %s (%s) – evicting", dev_id, exc
                    )
                    self.invalidate(dev_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _close_proto(proto: object) -> None:
        try:
            t = getattr(proto, "transport", None)
            if t and not t.is_closing():
                t.close()
        except Exception:
            pass

    @staticmethod
    def _fingerprint(d: dict) -> tuple:
        return (
            d.get("host"),
            d.get("device_id"),
            d.get("local_key"),
            str(d.get("protocol_version", 3.3)),
        )


# Singleton pool – created once; heartbeat is scheduled after the loop starts.
_conn_pool = DeviceConnectionPool()
asyncio.run_coroutine_threadsafe(_conn_pool.heartbeat(), loop)


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))


class QueueTuyaListener(TuyaListener):
    """Listener used by v3.4/v3.5 devices that report state via push updates."""

    sub_devices: dict[str, object] = {}

    def __init__(self, log_func=None):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.latest: dict = {}
        self._log = log_func

    def _record(self, message: str) -> None:
        if callable(self._log):
            self._log(message)

    def status_updated(self, status):
        self._record(f"PUSH RECEIVED via listener: {repr(status)[:200]}")
        if isinstance(status, dict):
            self.latest = status
        try:
            self.queue.put_nowait(status)
        except Exception:
            pass

    def disconnected(self, exc=""):
        self._record(f"Listener disconnected: {exc}")

    def subdevice_state_updated(self, state):
        pass


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def get_ha_config() -> dict:
    _log.debug("get_ha_config: reading %s", CONFIG_PATH)
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        _log.debug("get_ha_config: OK, %d entries", len(cfg.get("data", {}).get("entries", [])))
        return cfg
    except FileNotFoundError:
        _log.warning("get_ha_config: file not found: %s", CONFIG_PATH)
        return {}
    except Exception as exc:
        _log.error("get_ha_config: failed to read config: %s", exc)
        return {}


def get_devices_data() -> dict:
    ha = get_ha_config()
    for e in ha.get("data", {}).get("entries", []):
        if e.get("domain") == "localtuya":
            devices = e.get("data", {}).get("devices")
            if devices is None:
                _log.error(
                    "get_devices_data: localtuya entry found but 'devices' key missing. "
                    "Keys present: %s", list(e.get("data", {}).keys())
                )
                return {}
            _log.debug("get_devices_data: found %d devices", len(devices))
            return devices
    _log.warning("get_devices_data: no 'localtuya' domain entry found in config")
    return {}


def _extract_mac(val) -> str | None:
    if not val:
        return None
    if isinstance(val, str):
        v = val.strip().lower().replace("-", ":")
        if ":" in v:
            parts = [p.zfill(2) for p in v.split(":") if p != ""]
            if len(parts) == 6:
                return ":".join(parts)
        compact = "".join(ch for ch in v if ch.isalnum())
        if len(compact) == 12:
            return ":".join(compact[i : i + 2] for i in range(0, 12, 2))
        return v
    return None


def _build_cloud_conf() -> dict | None:
    ha_config = get_ha_config()
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            return entry.get("data")
    return None


def _lan_mac_for_ip(ip: str) -> str | None:
    """Best-effort MAC lookup for a local IPv4 address.
    
    Order:
    1) Query router via SSH (most reliable for containerized HA)
    2) /proc/net/arp  (fast, no extra deps)
    3) ``ip neigh show <ip>``  (requires iproute2)
    """
    if not ip or not isinstance(ip, str):
        return None
    ip = ip.strip()
    if not ip:
        return None

    # 1) Query router via SSH - this is the most reliable method for containerized HA
    try:
        router_key = "/config/.ssh/router_key"
        router_ip = "192.168.0.11"
        # Check ARP table on router
        cmd = [
            "ssh",
            "-i", router_key,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"root@{router_ip}",
            f"ip neigh show {ip}"
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
        if "lladdr" in out:
            mac = out.split("lladdr", 1)[1].strip().split()[0]
            mac_n = _extract_mac(mac)
            if mac_n and mac_n != "00:00:00:00:00:00":
                return mac_n
    except Exception:
        pass

    # 2) ARP cache (fallback)
    try:
        with open("/proc/net/arp", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 4 and parts[0] == ip:
                mac = parts[3]
                mac_n = _extract_mac(mac)
                if mac_n and mac_n != "00:00:00:00:00:00":
                    return mac_n
    except Exception:
        pass

    # 3) ip neigh (fallback)
    try:
        out = subprocess.check_output(
            ["ip", "neigh", "show", ip], text=True, stderr=subprocess.DEVNULL
        ).strip()
        if "lladdr" in out:
            mac = out.split("lladdr", 1)[1].strip().split()[0]
            return _extract_mac(mac)
    except Exception:
        pass

    return None


async def _fetch_cloud_devices(cloud_conf: dict) -> dict:
    _log.debug("_fetch_cloud_devices: connecting to Tuya Cloud (region=%s)", cloud_conf.get("region"))
    t0 = time.monotonic()
    api = TuyaCloudApi(
        cloud_conf["region"],
        cloud_conf["client_id"],
        cloud_conf["client_secret"],
        cloud_conf["user_id"],
    )
    await api.async_connect()
    _log.debug("_fetch_cloud_devices: connected, fetching device list…")
    devs = await api.async_get_devices_list(force_update=True)
    elapsed = time.monotonic() - t0
    _log.info("_fetch_cloud_devices: done in %.2fs, raw type=%s", elapsed, type(devs).__name__)
    if isinstance(devs, dict):
        _log.debug("_fetch_cloud_devices: got %d devices", len(devs))
        return devs
    if isinstance(getattr(api, "device_list", None), dict):
        return api.device_list
    if isinstance(getattr(api, "devices", None), dict):
        return api.devices
    return {}


CLOUD_DEVICE_CACHE_SECONDS = 300
_cloud_devices_cache: dict = {"updated_at": 0.0, "devices": {}}
_cloud_devices_lock = asyncio.Lock()
_cloud_functions_cache: dict[str, dict] = {}
_cloud_functions_updated_at: dict[str, float] = {}
_cloud_functions_lock = asyncio.Lock()


async def _get_cloud_devices_cached(force_update: bool = False) -> dict:
    if TuyaCloudApi is None:
        return {}
    cloud_conf = _build_cloud_conf()
    if not cloud_conf:
        return {}

    now = time.monotonic()
    async with _cloud_devices_lock:
        if (
            not force_update
            and _cloud_devices_cache["devices"]
            and now - _cloud_devices_cache["updated_at"] < CLOUD_DEVICE_CACHE_SECONDS
        ):
            return _cloud_devices_cache["devices"]

        try:
            devices = await _fetch_cloud_devices(cloud_conf)
        except Exception:
            return _cloud_devices_cache["devices"] or {}

        if isinstance(devices, dict):
            _cloud_devices_cache["devices"] = devices
            _cloud_devices_cache["updated_at"] = now
            return devices
        return {}


async def _connection_config(dev_id: str, d: dict, force_cloud_update: bool = False) -> dict:
    """Return device config with a fresh cloud local_key when available."""
    cfg = dict(d)
    cloud_devices = await _get_cloud_devices_cached(force_cloud_update)
    cloud = (
        cloud_devices.get(cfg.get("device_id"))
        or cloud_devices.get(cfg.get("gwId"))
        or cloud_devices.get(dev_id)
    )

    if isinstance(cloud, dict):
        cloud_key = cloud.get("local_key")
        if (
            isinstance(cloud_key, str)
            and len(cloud_key) == 16
            and cloud_key != cfg.get("local_key")
        ):
            cfg["local_key"] = cloud_key
            cfg["_cloud_key_refreshed"] = True
    return cfg


def _negotiation_failed(logs: str) -> bool:
    return "session key negotiation failed on step 1" in logs.lower()


def _parse_function_values(funcs: dict) -> dict:
    parsed = {}
    for dp_id, info in (funcs or {}).items():
        if not isinstance(info, dict):
            continue
        item = dict(info)
        values = item.get("values")
        if isinstance(values, str):
            try:
                item["values"] = json.loads(values)
            except Exception:
                pass
        parsed[str(dp_id)] = item
    return parsed


async def _get_cloud_functions_cached(
    dev_id: str, cfg: dict, force_update: bool = False
) -> dict:
    if TuyaCloudApi is None:
        return {}
    cloud_conf = _build_cloud_conf()
    if not cloud_conf:
        return {}

    cloud_id = cfg.get("device_id") or cfg.get("gwId") or dev_id
    now = time.monotonic()
    async with _cloud_functions_lock:
        if (
            not force_update
            and cloud_id in _cloud_functions_cache
            and now - _cloud_functions_updated_at.get(cloud_id, 0) < CLOUD_DEVICE_CACHE_SECONDS
        ):
            return _cloud_functions_cache[cloud_id]

        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            funcs = await api.async_get_device_functions(cloud_id)
        except Exception:
            return _cloud_functions_cache.get(cloud_id, {})
        funcs = _parse_function_values(funcs or {})
        _cloud_functions_cache[cloud_id] = funcs
        _cloud_functions_updated_at[cloud_id] = now
        return funcs


def _local_scaling_by_dp(cfg: dict) -> dict:
    scalings = {}
    for entity in cfg.get("entities", []):
        if not isinstance(entity, dict) or entity.get("id") is None:
            continue
        if entity.get("scaling") is not None:
            scalings[str(entity["id"])] = entity.get("scaling")
    return scalings


def _scale_display_value(value, scale):
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"unknown", "unavailable", "none", ""}:
            return value
        try:
            value = float(value) if "." in value else int(value)
        except ValueError:
            return value
    if not isinstance(value, (int, float)):
        return value
    try:
        scale = int(scale or 0)
    except (TypeError, ValueError):
        scale = 0
    if scale <= 0:
        return value
    scaled = value / (10 ** scale)
    return round(scaled, scale)


def _display_status_from_model(
    status: dict, cfg: dict, funcs: dict, already_scaled_dps: set[str] | None = None
) -> tuple[dict, dict]:
    """Apply Tuya data-model scale to values for display only."""
    already_scaled_dps = already_scaled_dps or set()
    display = {}
    units = {}
    for dp_id, value in (status or {}).items():
        dp = str(dp_id)
        info = funcs.get(dp, {}) if isinstance(funcs, dict) else {}
        values = info.get("values") if isinstance(info, dict) else {}
        if not isinstance(values, dict):
            values = {}

        units[dp] = values.get("unit") or ""
        # Values read from HA state storage may already be scaled by LocalTuya.
        # LAN status and Tuya Cloud status are raw Tuya DP values and must still
        # be scaled for display even when the LocalTuya entity has scaling set.
        if dp in already_scaled_dps:
            display[dp] = value
        else:
            display[dp] = _scale_display_value(value, values.get("scale"))
    return display, units


def _read_json(path: Path, fallback):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def _coerce_ha_state(state: dict):
    attrs = state.get("attributes") or {}
    if "raw_state" in attrs:
        return attrs["raw_state"]

    value = state.get("state")
    if value is None:
        return None
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    low = stripped.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in {"unknown", "unavailable", "none", ""}:
        return low

    try:
        if "." in stripped:
            return float(stripped)
        return int(stripped)
    except ValueError:
        return value


def _ha_states_as_dps(dev_id: str, cfg: dict) -> dict:
    """Return LocalTuya entity states keyed by DP id from HA storage."""
    registry = _read_json(ENTITY_REGISTRY_PATH, {})
    restore = _read_json(RESTORE_STATE_PATH, {})
    print(f"[DEBUG] ENTITY_REGISTRY_PATH: {ENTITY_REGISTRY_PATH}")
    print(f"[DEBUG] registry keys: {list(registry.get('data', {}).get('entities', [])[:2])}")
    
    entities = registry.get("data", {}).get("entities", [])
    restore_items = restore.get("data", []) if isinstance(restore, dict) else []

    entity_states = {}
    for item in restore_items:
        state = item.get("state") if isinstance(item, dict) else None
        if isinstance(state, dict) and state.get("entity_id"):
            entity_states[state["entity_id"]] = state

    device_id = cfg.get("device_id") or cfg.get("gwId") or dev_id
    wanted_dps = {
        str(entity.get("id"))
        for entity in cfg.get("entities", [])
        if isinstance(entity, dict) and entity.get("id") is not None
    }

    dps = {}
    prefix = f"local_{device_id}_"
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        unique_id = entity.get("unique_id")
        if not isinstance(unique_id, str) or not unique_id.startswith(prefix):
            continue

        dp_id = unique_id.removeprefix(prefix)
        if wanted_dps and dp_id not in wanted_dps:
            continue

        state = entity_states.get(entity.get("entity_id"))
        if not state:
            continue

        dps[dp_id] = _coerce_ha_state(state)

    return dps


async def _cloud_status_as_dps(dev_id: str, cfg: dict) -> dict:
    """Return current Tuya Cloud status keyed by DP id.

    Some Tuya firmwares accept LAN session-key negotiation but reject local
    DP_QUERY_NEW with retcode=1.  For read-only views, cloud status is still
    useful when the local query returns no DPS.
    """
    if TuyaCloudApi is None:
        return {}
    cloud_conf = _build_cloud_conf()
    if not cloud_conf:
        return {}

    cloud_devices = await _get_cloud_devices_cached(force_update=True)
    cloud_id = cfg.get("device_id") or cfg.get("gwId") or dev_id
    funcs = await _get_cloud_functions_cached(dev_id, cfg, force_update=True)
    if not isinstance(funcs, dict):
        funcs = {}

    dps = {
        str(dp_id): info.get("value")
        for dp_id, info in funcs.items()
        if isinstance(info, dict) and "value" in info
    }

    cloud = cloud_devices.get(cloud_id) or cloud_devices.get(dev_id) or {}
    status_items = cloud.get("status") if isinstance(cloud, dict) else None
    if not isinstance(status_items, list):
        return dps

    code_to_dp = {
        info.get("code"): str(dp_id)
        for dp_id, info in funcs.items()
        if isinstance(info, dict) and info.get("code")
    }

    for item in status_items:
        if not isinstance(item, dict):
            continue
        dp_id = code_to_dp.get(item.get("code"))
        if dp_id:
            dps[dp_id] = item.get("value")
    return dps


def load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sort_order": "name", "usage": {}}


def save_settings(s: dict) -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_PATH.open("w", encoding="utf-8") as f:
            json.dump(s, f)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# HTML template (unchanged from v1.1.3)
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Tuya Manager v{{ version }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, sans-serif; line-height: 1.4; color: #333; max-width: 1200px; margin: 0 auto; padding: 15px; background: #f0f2f5; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; background: #2c3e50; color: white; padding: 10px 20px; border-radius: 8px; }
        .tabs { display:flex; gap:8px; margin-bottom:10px; }
        .tab-btn { background:#6c757d; color:#fff; border:none; border-radius:6px; padding:8px 12px; cursor:pointer; font-weight:700; }
        .tab-btn.active { background:#007bff; }
        .tab-content { display:none; }
        .tab-content.active { display:flex; }
        .container { gap: 15px; height: 85vh; }
        .sidebar { flex: 1; display: flex; flex-direction: column; gap: 10px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .main { flex: 2.5; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow-y: auto; }
        .list { overflow-y: auto; flex: 1; border: 1px solid #eee; }
        .item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
        .item:hover { background: #f8f9fa; }
        .item.active { background: #e7f1ff; border-left: 4px solid #007bff; }
        .item.dup-name { background: #fff3cd; }
        .item.dup-name:hover { background: #ffe8a1; }
        .badge { display:inline-block; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:700; margin-left:6px; }
        .badge-warn { background:#856404; color:#fff; }
        .status-area { flex: 1; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; background: white; position: relative; }
        .overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.8); display: flex; align-items: center; justify-content: center; z-index: 10; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th { background: #f8f9fa; text-align: left; padding: 6px; border-bottom: 2px solid #dee2e6; position: sticky; top: 0; z-index: 5; }
        td { padding: 6px; border-bottom: 1px solid #eee; }
        .tech-logs { font-size: 11px; margin-top: 10px; height: 180px; overflow-y: auto; background: #1e1e1e; color: #00ff00; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }
        .controls { margin-top: 15px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; padding-top: 15px; border-top: 1px solid #eee; }
        button { padding: 8px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; color: white; font-size: 12px; }
        .btn-refresh { background: #28a745; }
        .btn-send { background: #007bff; }
        .btn-cloud { background: #17a2b8; }
        .primary-btn { background: #007bff; color: white; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer; font-weight: bold; font-size: 12px; transition: background 0.2s, opacity 0.2s; }
        .primary-btn:hover:not(:disabled) { background: #0056b3; }
        .primary-btn:disabled { background: #6c757d; color: #adb5bd; cursor: not-allowed; opacity: 0.65; }
        input, select { padding: 6px; border: 1px solid #ccc; border-radius: 4px; width: 100%; box-sizing: border-box; font-size: 12px; }
        label { font-size: 10px; font-weight: bold; color: #666; display: block; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="header"><h2>Tuya Manager</h2><span>v{{ version }}</span></div>
    <div class="tabs">
        <button id="tabManageBtn" class="tab-btn active" onclick="switchTab('manage')">Manage devices</button>
        <button id="tabAddBtn" class="tab-btn" onclick="switchTab('add')">Add new device</button>
        <button id="tabCloudBtn" class="tab-btn" onclick="switchTab('cloud')">Cloud Device Details</button>
        <button id="tabSpaceBtn" class="tab-btn" onclick="switchTab('space')">Space Management</button>
    </div>

    <div id="tabManage" class="container tab-content active">
        <div class="sidebar">
            <label>Sort</label>
            <select id="sort" onchange="updateSort(this.value)">
                <option value="name">Name</option><option value="ip">IP</option><option value="usage">Usage</option>
            </select>
            <div style="margin:10px 0;">
                <label>Search</label>
                <input type="text" id="deviceSearch" placeholder="Filter devices..." style="width:100%; padding:8px; margin-top:5px; box-sizing:border-box;" oninput="filterDevices()">
            </div>
            <div class="list" id="deviceList">Loading...</div>
        </div>
        <div class="main" id="details" style="display:none">
            <h3 id="name" style="margin:0"></h3>
            <p id="meta" style="font-size:11px; color:#666; margin:5px 0"></p>
            <div class="status-area">
                <div id="loadingOverlay" class="overlay hidden">WORKING...</div>
                <table id="dpTable">
                    <thead><tr><th>ID</th><th>Function</th><th>Value</th><th>Cloud Code</th></tr></thead>
                    <tbody id="dpBody"></tbody>
                </table>
            </div>
            <div class="tech-logs" id="techLogs">Ready.</div>
            <div class="controls">
                <div><label>DP ID</label><input type="number" id="dpId" onchange="updateValueInput()"></div>
                <div>
                    <label>Value</label>
                    <input type="text" id="dpValText">
                    <select id="dpValSelect" style="display:none"></select>
                </div>
                <div><label>Timeout</label><input type="number" id="timeout" value="90"></div>
                <div style="display:flex; align-items:flex-end;"><button class="btn-refresh" style="width:100%" onclick="refresh()">Refresh Local</button></div>
                <div style="grid-column: span 2;"><button class="btn-cloud" style="width:100%" onclick="cloudCheck()">Verify Cloud Response</button></div>
                <div style="grid-column: span 2;"><button class="btn-send" style="width:100%" id="sendBtn" onclick="send()">Send Command</button></div>
            </div>
        </div>
    </div>

    <div id="tabAdd" class="container tab-content">
        <div class="sidebar">
            <label>Manual Device Discovery</label>
            <div style="display:grid; grid-template-columns: 1fr auto; gap:8px; margin-bottom:12px;">
                <input type="text" id="manualDeviceIp" placeholder="e.g., 192.168.0.28" style="padding:8px; border:1px solid #ccc; border-radius:4px;">
                <button class="btn-refresh" style="padding:8px 12px;" onclick="discoverByIp()">Scan</button>
                <button class="btn-send" style="padding:8px 12px;" onclick="discoverByIpAdvanced()">Advanced Scan v3.4</button>
                <button class="btn-cloud" style="width:100%" onclick="forceFallback()">Force HA Fallback</button>
            </div>
            <div id="manualDiscoveryLogs" style="font-size:11px; color:#666; padding:8px; background:#f5f5f5; border-radius:4px; max-height:100px; overflow-y:auto; margin-bottom:12px; display:none;">
                Scanning...
            </div>

            <label style="margin-top:16px;">Cloud devices not yet configured</label>
            <div style="display:flex; gap:8px; margin-bottom:8px;">
                <button class="btn-cloud" style="flex:1" onclick="loadUnaddedDevices()">Refresh Unadded</button>
            </div>
            <div style="margin:8px 0;">
                <label>Search</label>
                <input type="text" id="unaddedSearch" placeholder="Filter unadded devices..." style="width:100%; padding:8px; margin-top:5px; box-sizing:border-box;" oninput="filterUnaddedDevices()">
            </div>
            <div class="list" id="unaddedList">Press "Refresh Unadded"</div>
        </div>
        <div class="main" id="unaddedDetails" style="display:none">
            <h3 id="unaddedName" style="margin:0"></h3>
            <p id="unaddedMeta" style="font-size:11px; color:#666; margin:5px 0"></p>
            <div class="status-area">
                <div id="unaddedLoadingOverlay" class="overlay hidden">WORKING...</div>
                <table>
                    <thead><tr><th>DP</th><th>Name</th><th>Code</th><th>Type</th><th>Values</th></tr></thead>
                    <tbody id="unaddedDpBody"></tbody>
                </table>
            </div>
            <div class="tech-logs" id="unaddedLogs">Ready.</div>
        </div>
    </div>

    <div id="tabCloud" class="container tab-content">
        <div class="sidebar">
            <label>All Cloud Devices</label>
            <div style="display:flex; gap:8px; margin-bottom:8px;">
                <button class="btn-cloud" style="flex:1" onclick="loadCloudDevices()">Refresh Cloud Devices</button>
            </div>
            <div style="margin:8px 0;">
                <label>Search</label>
                <input type="text" id="cloudSearch" placeholder="Filter cloud devices..." style="width:100%; padding:8px; margin-top:5px; box-sizing:border-box;" oninput="filterCloudDevices()">
            </div>
            <div class="list" id="cloudList">Press "Refresh Cloud Devices"</div>
        </div>
        <div class="main" id="cloudDetails" style="display:none">
            <h3 id="cloudName" style="margin:0"></h3>
            <p id="cloudMeta" style="font-size:11px; color:#666; margin:5px 0"></p>
            <div class="status-area">
                <div id="cloudLoadingOverlay" class="overlay hidden">WORKING...</div>
                <table>
                    <thead><tr><th>Field</th><th>Value</th></tr></thead>
                    <tbody id="cloudDetailBody"></tbody>
                </table>
            </div>
            <div class="tech-logs" id="cloudLogs">Ready.</div>
            <div style="margin-top:10px;">
                <label>Full JSON Export</label>
                <textarea id="cloudJsonOutput" rows="10" style="width:100%; padding:8px; margin-top:5px; box-sizing:border-box; font-family:monospace; font-size:11px;" readonly placeholder="Click 'Refresh Cloud Devices', select a device, then the JSON will appear here..."></textarea>
                <div style="display:flex; gap:8px; margin-top:8px;">
                    <button class="btn-cloud" style="flex:1" onclick="copyCloudJson()">Copy JSON</button>
                    <button class="btn-send" style="flex:1" onclick="downloadCloudJson()">Download JSON</button>
                </div>
</div>
</div>
</div>

    <!-- Custom Cloud Command Modal -->
    <div id="customCommandModal" class="overlay hidden" style="z-index:1000; background:rgba(0,0,0,0.7);">
        <div style="background:white; max-width:600px; margin:50px auto; padding:20px; border-radius:8px; position:relative;">
            <button onclick="closeCustomCommandModal()" style="position:absolute; top:10px; right:15px; background:none; border:none; font-size:20px; cursor:pointer; color:#333; z-index:10;">&times;</button>
            <h3 id="customCmdModalTitle">Custom Tuya Cloud Command</h3>
            <p style="font-size:12px; color:#666;">Device: <span id="customCmdDeviceName"></span> (ID: <span id="customCmdDeviceId"></span>)</p>
            <div style="margin:15px 0;">
                <label>Preset API Calls</label>
                <select id="customCmdPreset" style="width:100%; padding:8px; margin-top:5px;" onchange="applyPreset(this.value)">
                    <option value="">-- Select a preset --</option>
                    <optgroup label="Device Info">
                        <option value="GET|/v1.0/devices/{device_id}">Get Device Info</option>
                        <option value="GET|/v1.0/devices/{device_id}/status">Get Device Status</option>
                        <option value="GET|/v1.0/devices/{device_id}/functions">Get Device Functions</option>
                        <option value="GET|/v1.0/iot-03/devices/factory-infos?device_ids={device_id}">Get Factory Info (SN, MAC, UUID)</option>
                    </optgroup>
                    <optgroup label="Commands">
                        <option value='POST|/v1.0/devices/{device_id}/commands|{"commands":[{"code":"switch_1","value":true}]}'>Turn ON (switch_1)</option>
                        <option value='POST|/v1.0/devices/{device_id}/commands|{"commands":[{"code":"switch_1","value":false}]}'>Turn OFF (switch_1)</option>
                    </optgroup>
                    <optgroup label="Device Management">
                        <option value="GET|/v1.0/expand/devices/{device_id}">Expand Device Details (requires subscription)</option>
                    </optgroup>
                </select>
            </div>
            <div style="margin:15px 0;">
                <label>HTTP Method</label>
                <select id="customCmdMethod" style="width:100%; padding:8px; margin-top:5px;">
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                </select>
            </div>
            <div style="margin:15px 0;">
                <label>API Path</label>
                <input type="text" id="customCmdPath" placeholder="/v1.0/expand/devices/{device_id}" style="width:100%; padding:8px; margin-top:5px; box-sizing:border-box;">
            </div>
            <div style="margin:15px 0;">
                <label>Request Body (JSON, for POST/PUT)</label>
                <textarea id="customCmdBody" rows="5" placeholder='{"commands": [{"code": "switch_1", "value": true}]}' style="width:100%; padding:8px; margin-top:5px; box-sizing:border-box; font-family:monospace; font-size:12px;"></textarea>
            </div>
            <div style="display:flex; gap:10px;">
                <button class="btn-send" style="flex:1" onclick="sendCustomCloudCommand()">Send Command</button>
                <button class="btn-refresh" style="flex:1" onclick="closeCustomCommandModal()">Cancel</button>
            </div>
            <div style="margin-top:15px;">
                <label>Response</label>
                <div id="customCmdResponse" style="background:#f5f5f5; padding:10px; border-radius:4px; font-family:monospace; font-size:11px; max-height:200px; overflow:auto; white-space:pre-wrap;"></div>
            </div>
        </div>
    </div>

    <!-- Space Management Tab -->
    <div id="tabSpace" class="container tab-content">
        <div class="sidebar">
            <h3>Space Management</h3>
            <div class="space-selector">
                <label>Select Space from Tuya Cloud:</label>
                <div id="space-options" class="space-options">
                    <!-- Space options will be populated dynamically -->
                </div>
                <button id="select-space-btn" class="primary-btn" disabled>Get devices</button>
            </div>
            
            <div id="spaceResourcesContainer" class="hidden" style="margin-top: 20px;">
                <h3>Available Devices in Selected Space:</h3>
                <div id="spaceDevicesList" class="device-list">
                    <!-- New devices will be listed here -->
                </div>
                <button id="configure-devices-btn" class="primary-btn">Configure New Devices</button>
                <div id="rawPayloadSection" style="margin-top: 15px;">
                    <h5 style="margin: 0 0 8px 0;">Raw Space Resources (LocalTuya Format)</h5>
                    <textarea id="rawPayloadJson" readonly style="width: 100%; height: 200px; font-family: monospace; font-size: 11px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: #fff; resize:none; overflow:auto;">No raw payload yet. Select a space to fetch.</textarea>
                    <br>
                    <button id="copyRawPayloadBtn" class="primary-btn" style="margin-top: 8px; margin-right: 10px; padding: 6px 14px; font-size: 12px;">📋 Copy Raw JSON</button>
                    <button id="downloadRawPayloadBtn" class="btn-send" style="margin-top: 8px; padding: 6px 14px; font-size: 12px;">💾 Download Raw JSON</button>
                    <span id="rawPayloadStatus" style="font-size: 11px; color: #666; margin-left: 10px;"></span>
                </div>
                <div id="batchDevicesSection" class="hidden" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0;">Batch Device Details</h4>
                    <textarea id="deviceIdsTextbox" style="width: 100%; height: 80px; font-family: monospace; font-size: 12px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px;" placeholder="Paste or type device IDs separated by commas..."></textarea>
                    <br>
                    <button id="fetchDetailsBtn" class="primary-btn" style="margin-right: 10px;">Get device IDs</button>
                    <button id="copyIdsBtn" class="btn-send" style="margin-right: 10px;">📋 Copy IDs</button>
                    <span id="batchStatus" style="font-size: 12px; color: #666;"></span>
                </div>
                <div id="batchResultSection" style="margin-top: 15px;">
                    <h5 style="margin: 0 0 8px 0;">Merged Device Config JSON</h5>
                    <textarea id="batchResultJson" readonly style="width: 100%; height: 200px; font-family: monospace; font-size: 11px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: #fff; resize:none; overflow:auto;">No results yet. Select a space and click "Get device IDs".</textarea>
                    <br>
                    <button id="copyBatchJsonBtn" class="primary-btn" style="margin-top: 8px; margin-right: 10px; padding: 6px 14px; font-size: 12px;">📋 Copy JSON</button>
                    <button id="downloadBatchJsonBtn" class="btn-send" style="margin-top: 8px; padding: 6px 14px; font-size: 12px;">💾 Download JSON</button>
                </div>
            </div>
        </div>
        <div class="main" id="spaceDetails" style="display:none">
            <h3>Space Details</h3>
            <div id="space-info-content">
                <!-- Space details will be displayed here -->
            </div>
            <div class="tech-logs" id="spaceLogs">Ready.</div>
        </div>
    </div>
    <script>
        let devices = {}; let currentDps = {}; let currentDisplayDps = {}; let currentDisplayUnits = {}; let cloudDps = {}; let selectedId = null; let currentSort = "name";
        let unaddedDevices = {}; let selectedUnaddedId = null;
        function deviceDisplayName(d, fallbackId) {
            if(!d) return fallbackId;
            return d.friendly_name || d.name || d.local_name || fallbackId;
        }
        function managedNameSet() {
            const set = new Set();
            Object.keys(devices || {}).forEach(id => {
                const n = deviceDisplayName(devices[id], id);
                if(n) set.add(String(n).trim().toLowerCase());
            });
            return set;
        }
        function switchTab(tab) {
            const isManage = tab === 'manage';
            const isAdd = tab === 'add';
            const isCloud = tab === 'cloud';
            const isSpace = tab === 'space';
            document.getElementById('tabManage').classList.toggle('active', isManage);
            document.getElementById('tabAdd').classList.toggle('active', isAdd);
            document.getElementById('tabCloud').classList.toggle('active', isCloud);
            document.getElementById('tabSpace').classList.toggle('active', isSpace);
            document.getElementById('tabManageBtn').classList.toggle('active', isManage);
            document.getElementById('tabAddBtn').classList.toggle('active', isAdd);
            document.getElementById('tabCloudBtn').classList.toggle('active', isCloud);
            document.getElementById('tabSpaceBtn').classList.toggle('active', isSpace);
            
            // Initialize space management when tab is selected
            if (isSpace) {
                console.log('[tuya_gui] Space Management tab selected, calling loadSpaces()');
                loadSpaces();
            }
        }
        async function init() {
            console.log('[tuya_gui] init: start');
            try {
                const s = await (await fetch('/api/settings')).json();
                currentSort = s.sort_order || "name";
                document.getElementById('sort').value = currentSort;
                console.log('[tuya_gui] init: settings OK, sort=', currentSort);
            } catch(e) {
                console.error('[tuya_gui] init: failed to load settings', e);
            }

            // Restore cached values from localStorage
            const cachedDeviceIds = localStorage.getItem('tuyaGui_deviceIds');
            if (cachedDeviceIds) {
                const tb = document.getElementById('deviceIdsTextbox');
                if (tb) tb.value = cachedDeviceIds;
            }
            const cachedBatchResult = localStorage.getItem('tuyaGui_batchResult');
            if (cachedBatchResult) {
                const rb = document.getElementById('batchResultJson');
                if (rb) rb.value = cachedBatchResult;
            }
            const cachedRawPayload = localStorage.getItem('tuyaGui_rawPayload');
            if (cachedRawPayload) {
                const rp = document.getElementById('rawPayloadJson');
                if (rp) rp.value = cachedRawPayload;
            }

            // Attach click handler for Space Management "Get devices" button
            const selectSpaceBtn = document.getElementById('select-space-btn');
            if (selectSpaceBtn) {
                selectSpaceBtn.addEventListener('click', handleSpaceSelection);
                console.log('[tuya_gui] init: Get devices button click handler attached');
            } else {
                console.warn('[tuya_gui] init: select-space-btn NOT found in DOM at init');
            }
            
            loadDevices();
        }
        async function loadDevices() {
            console.log('[tuya_gui] loadDevices: start');
            const listEl = document.getElementById('deviceList');
            try {
                const r = await fetch('/api/devices');
                console.log('[tuya_gui] loadDevices: /api/devices HTTP', r.status);
                if (!r.ok) {
                    const text = await r.text();
                    console.error('[tuya_gui] loadDevices: server error', r.status, text);
                    listEl.innerHTML = `<div style="color:red;padding:10px">Server error ${r.status}:<br><pre style="font-size:10px;white-space:pre-wrap">${text.slice(0,500)}</pre></div>`;
                    return;
                }
                const data = await r.json();
                console.log('[tuya_gui] loadDevices: data received, devices=', Object.keys(data.devices||{}).length, 'error=', data.error||null);
                if (data.error) {
                    console.warn('[tuya_gui] loadDevices: server returned error:', data.error);
                }
                devices = data.devices || {};
                const usage = data.usage || {};
                const keys = Object.keys(devices).sort((a,b) => {
                    if(currentSort === 'usage') return (usage[b]||0) - (usage[a]||0);
                    if(currentSort === 'ip') {
                        const aLocal = devices[a].local_ip || devices[a].host || '';
                        const bLocal = devices[b].local_ip || devices[b].host || '';
                        const aCloud = devices[a].cloud_ip || '';
                        const bCloud = devices[b].cloud_ip || '';
                        return (aLocal + '|' + aCloud).localeCompare(bLocal + '|' + bCloud);
                    }
                    return (devices[a].friendly_name || '').localeCompare(devices[b].friendly_name || '');
                });
                if (keys.length === 0) {
                    const errMsg = data.error ? `<br><span style="color:red">Error: ${data.error}</span>` : '';
                    listEl.innerHTML = `<div style="padding:10px;color:#666">No devices found.${errMsg}</div>`;
                } else {
                    listEl.innerHTML = keys.map(k => `
                        <div class="item ${selectedId===k?'active':''}" onclick="select(${JSON.stringify(k)})">
                            <strong>${devices[k].friendly_name || k}</strong><br>
                            <small>local: ${(devices[k].local_ip || devices[k].host || 'no local ip')} | cloud: ${(devices[k].cloud_ip || 'no cloud ip')} | mac: ${(devices[k].match_mac || devices[k].mac || '-') }</small>
                            <button style="float:right; margin-top:-20px; padding:4px 8px; font-size:10px; background:#6f42c1; color:white; border:none; border-radius:3px; cursor:pointer;" onclick="event.stopPropagation(); openCustomCommandModal('${k}')">☁ Custom CMD</button>
                        </div>
                    `).join('');
                }
                console.log('[tuya_gui] loadDevices: rendered', keys.length, 'devices');
            } catch(e) {
                console.error('[tuya_gui] loadDevices: exception', e);
                listEl.innerHTML = `<div style="color:red;padding:10px">Failed to load devices:<br>${e}</div>`;
            }
        }
        function select(id) {
            selectedId = id; const d = devices[id];
            document.getElementById('details').style.display = 'flex';
            document.getElementById('name').innerText = d.friendly_name || id;
            document.getElementById('meta').innerText = `ID: ${id} | Local IP: ${(d.local_ip || d.host || 'N/A')} | Cloud IP: ${(d.cloud_ip || 'N/A')} | MAC: ${(d.match_mac || d.mac || 'N/A')}`;
            document.querySelectorAll('.item').forEach(el => el.classList.remove('active'));
            refresh();
        }
        async function refresh() {
            if(!selectedId) return;
            const overlay = document.getElementById('loadingOverlay'); overlay.classList.remove('hidden');
            try {
                const r = await fetch(`/api/device/${selectedId}/status?timeout=${document.getElementById('timeout').value}`);
                const data = await r.json();
                document.getElementById('techLogs').innerText = data.tech_logs || "No data.";
                if (!data.error) {
                    currentDps = data.status || {};
                    currentDisplayDps = data.display_status || currentDps;
                    currentDisplayUnits = data.display_units || {};
                    const src = data.source || 'local';
                    const srcColor = src === 'local' ? '#28a745' : src === 'local-push' ? '#17a2b8' : '#856404';
                    document.getElementById('meta').innerHTML = document.getElementById('meta').innerText.split('|').slice(0,4).join('|') +
                        ` | <b style="color:${srcColor}">source: ${src}</b>`;
                    renderTable();
                }
                else { alert(data.error); }
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }
        async function cloudCheck() {
            if(!selectedId) return;
            const overlay = document.getElementById('loadingOverlay'); overlay.classList.remove('hidden');
            const logsBox = document.getElementById('techLogs');
            logsBox.innerText = "Querying Tuya Cloud...\\n";
            try {
                const r = await fetch(`/api/device/${selectedId}/cloud_check`);
                const data = await r.json();
                logsBox.innerText = data.tech_logs || "";
                if (!data.error) { 
                    cloudDps = data.result || {}; 
                    if (data.status) {
                        currentDps = data.status || {};
                        currentDisplayDps = data.display_status || currentDps;
                        currentDisplayUnits = data.display_units || {};
                    }
                    logsBox.innerText += "\\n\\n--- CLOUD JSON RESULT ---\\n" + JSON.stringify(data.result, null, 2);
                    renderTable(); 
                } else { alert(data.error); }
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }

        function cloudValueFromInfo(id) {
            const info = cloudDps[id] || {};
            return Object.prototype.hasOwnProperty.call(info, 'value') ? info.value : undefined;
        }

        function renderTable() {
            const mapping = devices[selectedId].entities || [];
            const allIds = new Set([...Object.keys(currentDps), ...Object.keys(cloudDps)]);
            document.getElementById('dpBody').innerHTML = Array.from(allIds).sort((a,b)=>Number(a)-Number(b)).map(id => {
                const cloudValue = cloudValueFromInfo(id);
                const rawVal = currentDps[id] !== undefined ? currentDps[id] : cloudValue;
                const displayVal = currentDisplayDps[id] !== undefined ? currentDisplayDps[id] : rawVal;
                const unit = currentDisplayUnits[id] ? ` ${currentDisplayUnits[id]}` : '';
                let valStr = '';
                if (rawVal === undefined || rawVal === null) valStr = '';
                else if (typeof rawVal === 'object') valStr = JSON.stringify(rawVal);
                else valStr = String(rawVal);
                const localVal = rawVal !== undefined ? `${displayVal}${unit}` : '<span style="color:#999">?</span>';
                const cloudInfo = cloudDps[id] || {};
                const entity = mapping.find(e => e.id == id);
                // Passa valStr (stringa sicura) al click
                return `<tr onclick="onRowClick(${JSON.stringify(id)}, ${JSON.stringify(valStr)})" style="cursor:pointer">
                    <td><b>${id}</b></td>
                    <td>${entity ? entity.friendly_name : (cloudInfo.name || 'Unknown')}</td>
                    <td>${localVal}</td>
                    <td><small>${cloudInfo.code || '-'}</small></td>
                </tr>`;
            }).join('');
            updateValueInput();
        }

        function onRowClick(id, val) {
            document.getElementById('dpId').value = id;
            updateValueInput(val);
        }
        function updateValueInput(valOverride = null) {
            if(!selectedId) return;
            const dpId = document.getElementById('dpId').value;
            const textInput = document.getElementById('dpValText');
            const selectDiv = document.getElementById('dpValSelect');
            const cloudInfo = cloudDps[dpId] || {};
            const entity = (devices[selectedId].entities || []).find(e => e.id == dpId);
            const curVal = valOverride !== null ? valOverride : currentDps[dpId];

            let options = null;
            if(cloudInfo.values && cloudInfo.values.type === 'enum') {
                options = {}; cloudInfo.values.range.forEach(v => options[v] = v);
            } else if(cloudInfo.values && cloudInfo.values.type === 'boolean') {
                options = {"true": "ON", "false": "OFF"};
            } else if(entity && entity.select_options) {
                options = entity.select_options;
            } else if(curVal === true || curVal === false || curVal === 'true' || curVal === 'false') {
                options = {"true": "ON", "false": "OFF"};
            }

            if(options) {
                textInput.style.display = 'none'; selectDiv.style.display = 'block';
                selectDiv.innerHTML = Object.keys(options).map(k => `<option value="${k}" ${String(curVal)===String(k)?'selected':''}>${options[k]}</option>`).join('');
            } else {
                textInput.style.display = 'block'; selectDiv.style.display = 'none';
                if(valOverride !== null) textInput.value = valOverride;
            }
        }
        async function updateSort(v) { 
            currentSort = v; 
            await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({sort_order:v})});
            loadDevices(); 
        }
        async function send() {
            const dpId = document.getElementById('dpId').value;
            const val = document.getElementById('dpValSelect').style.display === 'none' ? document.getElementById('dpValText').value : document.getElementById('dpValSelect').value;
            let finalVal = val;
            if(val.toLowerCase()==='true') finalVal = true;
            else if(val.toLowerCase()==='false') finalVal = false;
            else if(!isNaN(val) && val.trim()!=='') finalVal = Number(val);
            const overlay = document.getElementById('loadingOverlay'); overlay.classList.remove('hidden');
            try {
                await fetch(`/api/device/${selectedId}/command`, {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({ dps:{[dpId]:finalVal}, timeout:document.getElementById('timeout').value })
                });
                refresh();
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }

        async function forceFallback() {
            if(!selectedId) return;
            const overlay = document.getElementById('loadingOverlay');
            overlay.classList.remove('hidden');
            try {
                const r = await fetch(`/api/device/${selectedId}/force_ha`);
                const data = await r.json();
                document.getElementById('techLogs').innerText = data.tech_logs || "No data.";
                if (!data.error) {
                    currentDps = data.status || {};
                    currentDisplayDps = data.display_status || currentDps;
                    currentDisplayUnits = data.display_units || {};
                    renderTable();
                } else { alert(data.error); }
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }

        // Custom Cloud Command Modal Functions
        function openCustomCommandModal(deviceId) {
            if(!deviceId && !selectedId) return;
            const id = deviceId || selectedId;
            const d = devices[id];
            document.getElementById('customCmdDeviceName').innerText = d.friendly_name || id;
            document.getElementById('customCmdDeviceId').innerText = id;
            document.getElementById('customCmdPreset').value = '';
            document.getElementById('customCmdPath').value = `/v1.0/expand/devices/${id}`;
            document.getElementById('customCmdBody').value = JSON.stringify({
  "commands": [
    {"code": "switch_1", "value": true}
  ]
}, null, 2);
            document.getElementById('customCmdResponse').innerText = '';
            document.getElementById('customCommandModal').classList.remove('hidden');
        }

        function applyPreset(value) {
            if (!value) return;
            const parts = value.split('|');
            const method = parts[0];
            const path = parts[1];
            const body = parts[2] || '';
            
            document.getElementById('customCmdMethod').value = method;
            document.getElementById('customCmdPath').value = path.replace('{device_id}', document.getElementById('customCmdDeviceId').innerText);
            document.getElementById('customCmdBody').value = body;
        }

        function closeCustomCommandModal() {
            document.getElementById('customCommandModal').classList.add('hidden');
        }

        async function sendCustomCloudCommand() {
            const deviceId = document.getElementById('customCmdDeviceId').innerText;
            if(!deviceId) return;
            const method = document.getElementById('customCmdMethod').value;
            const path = document.getElementById('customCmdPath').value;
            const bodyText = document.getElementById('customCmdBody').value;
            const responseDiv = document.getElementById('customCmdResponse');
            
            if (!path) {
                alert('API path is required');
                return;
            }

            // Clear response area immediately
            responseDiv.innerText = '';
            
            responseDiv.innerText = 'Sending...';
            
            let body = null;
            if (bodyText && (method === 'POST' || method === 'PUT')) {
                try {
                    body = JSON.parse(bodyText);
                } catch(e) {
                    responseDiv.innerText = 'Invalid JSON in body: ' + e.message;
                    return;
                }
            }

            try {
                const r = await fetch(`/api/device/${deviceId}/custom_cloud_request`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ method, path, body })
                });
                const data = await r.json();
                responseDiv.innerText = JSON.stringify(data, null, 2);
            } catch(e) {
                responseDiv.innerText = 'Error: ' + e.message;
            }
        }

        async function discoverByIp() {
            const ipInput = document.getElementById('manualDeviceIp');
            const ip = ipInput.value.trim();
            if (!ip) { alert('Enter an IP address'); return; }

            const logsDiv = document.getElementById('manualDiscoveryLogs');
            logsDiv.style.display = 'block';
            logsDiv.innerHTML = 'Scanning...';

            try {
                const r = await fetch('/api/device/discover_by_ip', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ ip: ip })
                });
                const data = await r.json();
                
                logsDiv.innerHTML = (data.tech_logs || '').split('\\n').map(l => l ? `<div>${l}</div>` : '').join('');

                if (data.error && !data.device) {
                    alert('Error: ' + data.error);
                    return;
                }

                if (data.device) {
                    const devId = data.device_id;
                    const dev = data.device;
                    
                    // Ricarica la lista dei dispositivi gestiti (potrebbe essere già presente)
                    await loadDevices();
                    
                    // Se l'ID è nella lista dei dispositivi gestiti, selezionalo direttamente
                    if (devices[devId]) {
                        switchTab('manage');
                        select(devId);
                        // Opzionale: mostra un messaggio di conferma
                        alert(`Device ${devices[devId].friendly_name || devId} selected. Check the DPs in the table below.`);
                        return;
                    }
                    
                    // Altrimenti, mostra i dettagli per configurazione manuale
                    let info = `Device found but not in managed list.\\n\\n`;
                    info += `Device ID: ${devId}\\n`;
                    info += `IP: ${dev.ip || dev.local_ip || ip}\\n`;
                    info += `Port: ${dev.port || 6668}\\n`;
                    if (dev.mac) info += `MAC: ${dev.mac}\\n`;
                    if (dev.local_key) info += `Local Key: ${dev.local_key}\\n`;
                    if (dev.product_name) info += `Product: ${dev.product_name}\\n`;
                    info += `\\nStatus: ${dev.status || 'unknown'}\\n`;
                    if (dev.note) info += `Note: ${dev.note}\\n`;
                    alert(info);
                    
                    // Se il dispositivo ha un local_key, possiamo aggiungerlo temporaneamente alla lista "unadded"?
                    // Per ora ci fermiamo qui.
                }
            } catch(e) {
                logsDiv.innerHTML = `<div style="color:red">Error: ${e}</div>`;
                alert('Discovery failed: ' + e);
            }
        }

        async function discoverByIpAdvanced() {
            const ip = document.getElementById('manualDeviceIp').value;
            if (!ip) { alert('IP address required'); return; }
            
            const logsDiv = document.getElementById('manualDiscoveryLogs');
            logsDiv.style.display = 'block';
            logsDiv.innerHTML = 'Starting Advanced Scan v3.4...';
            
            try {
                const r = await fetch('/api/device/discover_by_ip_advanced', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ip: ip})
                });
                const data = await r.json();
                
                logsDiv.innerHTML = (data.tech_logs || '').split('\\n').map(l => l ? `<div>${l}</div>` : '').join('');

                if (data.error && !data.device) {
                    alert('Error: ' + data.error);
                    return;
                }

                const localStatus = (data.device && data.device.local_test_status) || {};
                const cloudStatus = (data.device && data.device.cloud_test_status) || {};
                const localCount = Object.keys(localStatus).length;
                const cloudCount = Object.keys(cloudStatus).length;

                if (data.device && data.device.id) {
                    await loadDevices();
                    if (devices[data.device.id]) {
                        switchTab('manage');
                        selectedId = data.device.id;
                        document.getElementById('details').style.display = 'flex';
                        document.getElementById('name').innerText = devices[selectedId].friendly_name || selectedId;
                        document.getElementById('meta').innerText = `ID: ${selectedId} | Local IP: ${(devices[selectedId].local_ip || devices[selectedId].host || 'N/A')} | Cloud IP: ${(devices[selectedId].cloud_ip || 'N/A')} | MAC: ${(devices[selectedId].match_mac || devices[selectedId].mac || 'N/A')}`;
                        if (cloudCount) {
                            currentDps = cloudStatus;
                            currentDisplayDps = data.device.cloud_display_status || cloudStatus;
                            currentDisplayUnits = data.device.cloud_display_units || {};
                            renderTable();
                        }
                    }
                }

                if (localCount) {
                    alert(`✓ SUCCESS! Local data retrieved via v3.4 Push/Active Strategy:\n\n${JSON.stringify(data.device.local_test_status, null, 2)}`);
                } else if (cloudCount) {
                    alert(`Local polling failed, but Cloud returned ${cloudCount} DPS. The managed device view has been opened with Cloud values.\n\nNote: ${data.device.note || ''}`);
                } else if (data.device) {
                    alert(`Scan finished. Device found but local data polling failed even with advanced strategy.\n\nNote: ${data.device.note || ''}`);
                }
            } catch(e) {
                logsDiv.innerHTML = `<div style="color:red">Error: ${e}</div>`;
                alert('Advanced Discovery failed: ' + e);
            }
        }

        async function loadUnaddedDevices() {
            const list = document.getElementById('unaddedList');
            const logs = document.getElementById('unaddedLogs');
            list.innerHTML = 'Loading...';
            logs.innerText = 'Querying cloud devices...';
            try {
                const r = await fetch('/api/devices/unadded');
                const data = await r.json();
                logs.innerText = data.tech_logs || 'Done.';
                if (data.error) {
                    list.innerHTML = `<div class="item">Error: ${data.error}</div>`;
                    return;
                }
                unaddedDevices = data.devices || {};
                const mset = managedNameSet();
                const keys = Object.keys(unaddedDevices);
                if (!keys.length) {
                    list.innerHTML = '<div class="item">No unadded devices found.</div>';
                    return;
                }
                list.innerHTML = keys.map(k => {
                    const d = unaddedDevices[k] || {};
                    const localIp = d.local_ip || 'no local IP';
                    const cloudIp = d.cloud_ip || (d.ip || 'no cloud IP');
                    const mac = d.match_mac || d.mac || d.device_mac || '-';
                    const name = deviceDisplayName(d, k);
                    const isDup = mset.has(String(name).trim().toLowerCase());
                    const dupNote = 'Same name as an already managed device: it may be a different Tuya Cloud record (different deviceId/IP).';
                    return `<div class="item ${selectedUnaddedId===k?'active':''} ${isDup?'dup-name':''}" onclick="selectUnadded(${JSON.stringify(k)})">
                        <strong>${name}${isDup?'<span class="badge badge-warn">DUPLICATE NAME</span>':''}</strong><br>
                        <small>${d.product_name || d.category || '-'} | local: ${localIp} | cloud: ${cloudIp} | mac: ${mac}</small>
                        ${isDup?`<br><small style="color:#856404">${dupNote}</small>`:''}
                        <button style="float:right; margin-top:-20px; padding:4px 8px; font-size:10px; background:#6f42c1; color:white; border:none; border-radius:3px; cursor:pointer;" onclick="event.stopPropagation(); openCustomCommandModal('${k}')">☁ Custom CMD</button>
                    </div>`;
                }).join('');
            } catch(e) {
                list.innerHTML = `<div class="item">Error: ${e}</div>`;
            }
        }

        async function selectUnadded(devId) {
            selectedUnaddedId = devId;
            document.querySelectorAll('#unaddedList .item').forEach(el => el.classList.remove('active'));
            document.getElementById('unaddedDetails').style.display = 'flex';
            const d = unaddedDevices[devId] || {};
            document.getElementById('unaddedName').innerText = d.name || d.local_name || devId;
            document.getElementById('unaddedMeta').innerText = `ID: ${devId} | Category: ${d.category || '-'} | Product: ${d.product_name || '-'} | Local IP: ${d.local_ip || 'N/A'} | Cloud IP: ${d.cloud_ip || d.ip || 'N/A'} | MAC: ${d.match_mac || d.mac || d.device_mac || 'N/A'}`;
            const overlay = document.getElementById('unaddedLoadingOverlay');
            const logs = document.getElementById('unaddedLogs');
            overlay.classList.remove('hidden');
            logs.innerText = 'Loading cloud functions...';
            try {
                const r = await fetch(`/api/device/${devId}/cloud_check`);
                const data = await r.json();
                logs.innerText = data.tech_logs || '';
                if (data.error) {
                    document.getElementById('unaddedDpBody').innerHTML = `<tr><td colspan="5">Error: ${data.error}</td></tr>`;
                    return;
                }
                const funcs = data.result || {};
                const rows = Object.keys(funcs).sort().map(dpId => {
                    const info = funcs[dpId] || {};
                    const type = info.values && info.values.type ? info.values.type : '-';
                    const values = info.values ? JSON.stringify(info.values) : '-';
                    return `<tr>
                        <td><b>${dpId}</b></td>
                        <td>${info.name || '-'}</td>
                        <td><small>${info.code || '-'}</small></td>
                        <td>${type}</td>
                        <td><small>${values}</small></td>
                    </tr>`;
                });
                document.getElementById('unaddedDpBody').innerHTML = rows.length ? rows.join('') : '<tr><td colspan="5">No DP/functions returned.</td></tr>';
            } catch(e) {
                document.getElementById('unaddedDpBody').innerHTML = `<tr><td colspan="5">Error: ${e}</td></tr>`;
            } finally {
                overlay.classList.add('hidden');
            }
        }
        // Filter unadded devices
        function filterUnaddedDevices() {
            const input = document.getElementById('unaddedSearch');
            const filter = input.value.toLowerCase();
            const items = document.querySelectorAll('#unaddedList .item');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(filter) ? '' : 'none';
            });
        }

        // Filter managed devices
        function filterDevices() {
            const input = document.getElementById('deviceSearch');
            const filter = input.value.toLowerCase();
            const items = document.querySelectorAll('#deviceList .item');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(filter) ? '' : 'none';
            });
        }

// Cloud Devices Tab Functions
        async function loadCloudDevices() {
            const list = document.getElementById('cloudList');
            const logs = document.getElementById('cloudLogs');
            list.innerHTML = 'Loading...';
            logs.innerText = 'Querying Tuya Cloud...';
            try {
                const r = await fetch('/api/devices/cloud');
                const data = await r.json();
                logs.innerText = data.tech_logs || 'Done.';
                if (data.error) {
                    list.innerHTML = `<div class="item">Error: ${data.error}</div>`;
                    return;
                }
                cloudDevices = data.devices || {};
                const keys = Object.keys(cloudDevices);
                if (!keys.length) {
                    list.innerHTML = '<div class="item">No cloud devices found.</div>';
                    return;
                }
                list.innerHTML = keys.map(k => {
                    const d = cloudDevices[k] || {};
                    const localIp = d.local_ip || d.host || 'no local IP';
                    const cloudIp = d.cloud_ip || d.ip || 'no cloud IP';
                    const mac = d.match_mac || d.mac || d.device_mac || '-';
                    const name = d.friendly_name || d.name || k;
                    return `<div class="item" onclick="selectCloud(${JSON.stringify(k)})">
                        <strong>${name}</strong><br>
                        <small>${d.product_name || d.category || '-'} | local: ${localIp} | cloud: ${cloudIp} | mac: ${mac}</small>
                    </div>`;
                }).join('');
            } catch(e) {
                list.innerHTML = `<div class="item">Error: ${e}</div>`;
                logs.innerText = 'Error: ' + e;
            }
        }

        let cloudDevices = {};
        let selectedCloudId = null;
        let spaces = [];
        let selectedSpaceId = null;

        // Space management functions with detailed API logging
        async function loadSpaces() {
            console.log('=== SPACE MANAGEMENT: Loading Spaces ===');
            console.log('[loadSpaces] Function called, fetching from /api/cloud/spaces');
            try {
                console.log('Making API request to: /api/cloud/spaces');
                const response = await fetch('/api/cloud/spaces');
                console.log('API Response Status:', response.status);
                const data = await response.json();
                
                console.log('API Response Data:', JSON.stringify(data, null, 2));
                
                if (data.error) {
                    console.error('Error loading spaces:', data.error);
                    console.log('Tech logs:', data.tech_logs || '');
                    return;
                }
                
                spaces = data.spaces || [];
                console.log('✅ Successfully loaded spaces:', spaces);
                console.log('Total spaces found:', spaces.length);
                displaySpaceOptions();
            } catch (error) {
                console.error('Error loading spaces:', error);
                console.error('Error details:', error.stack || error.message);
            }
        }

        function displaySpaceOptions() {
            console.log('=== SPACE MANAGEMENT: Displaying Space Options ===');
            const container = document.getElementById('space-options');
            container.innerHTML = '';
            
            if (spaces.length === 0) {
                container.innerHTML = '<div class="no-spaces">No spaces found</div>';
                console.log('No spaces available for selection');
                return;
            }
            
            console.log('Creating space selection options for IDs:', spaces);
            
            spaces.forEach(spaceId => {
                const spaceElement = document.createElement('label');
                spaceElement.className = 'space-option';
                const isSelected = selectedSpaceId === spaceId;
                spaceElement.innerHTML = `
                    <input type="radio" name="spaceId" value="${spaceId}" 
                           ${isSelected ? 'checked' : ''}>
                    <div>
                        <strong>Space: ${spaceId}</strong>
                        <small>Space ID from Tuya Cloud</small>
                    </div>
                `;
                
                if (isSelected) {
                    spaceElement.classList.add('selected');
                }
                
                spaceElement.querySelector('input').addEventListener('change', (e) => {
                    console.log('=== SPACE MANAGEMENT: Space Selection Changed ===');
                    console.log('Selected space ID:', e.target.value);
                    selectedSpaceId = e.target.value;
                    document.querySelectorAll('.space-option').forEach(el => {
                        el.classList.remove('selected');
                    });
                    spaceElement.classList.add('selected');
                    const btn = document.getElementById('select-space-btn');
                    console.log('[Radio] Button element found:', btn !== null, 'Current disabled:', btn ? btn.disabled : 'N/A');
                    if (btn) {
                        btn.disabled = false;
                        console.log('Space selection updated, button enabled');
                    } else {
                        console.error('❌ select-space-btn ("Get devices" button) NOT FOUND in DOM!');
                    }
                });
                
                container.appendChild(spaceElement);
                console.log('Added space option for ID:', spaceId);
            });
            
            console.log('✅ Space options display complete:', spaces.length, 'options created');
        }

        async function handleSpaceSelection() {
            console.log('=== SPACE MANAGEMENT: Handling Space Selection ===');
            console.log('[handleSpaceSelection] Function called, selectedSpaceId:', selectedSpaceId);
            
            if (!selectedSpaceId) {
                alert('Please select a space');
                console.log('❌ No space selected, showing error message');
                return;
            }
            
            const apiUrl = `/api/cloud/spaces/${selectedSpaceId}/resources`;
            console.log('Making API request to:', apiUrl);
            
            try {
                console.log('Fetching space resources...');
                const response = await fetch(apiUrl);
                console.log('API Response Status:', response.status);
                const data = await response.json();
                
                console.log('API Response Data:', JSON.stringify(data, null, 2));
                
                if (data.error) {
                    console.error('❌ Error loading space resources:', data.error);
                    console.log('Tech logs:', data.tech_logs || '');
                    alert('Error loading space resources: ' + data.error);
                    return;
                }
                
                const resources = data.resources || [];
                console.log('✅ Successfully loaded space resources:', resources.length, 'total');
                console.log('Sample resource data:', resources.length > 0 ? JSON.stringify(resources[0], null, 2) : 'No resources');
                
                // Filter for new devices (not already configured)
                console.log('=== SPACE MANAGEMENT: Filtering New Devices ===');
                const existingDevices = await getExistingDevices();
                console.log('Existing devices in system:', existingDevices);
                
                const newDevices = resources.filter(resource => {
                    // Use res_id as the device identifier from Tuya Cloud
                    const deviceId = resource.res_id || resource.device_id || resource.id || resource.deviceId;
                    const isNew = deviceId && !existingDevices.includes(deviceId);
                    console.log(`Checking resource - res_id: ${resource.res_id}, deviceId: ${deviceId}, res_type: ${resource.res_type}, Is New: ${isNew}`);
                    return isNew;
                });
                
                console.log('✅ Space filtering complete:');
                console.log('- Total resources:', resources.length);
                console.log('- New devices found:', newDevices.length);
                console.log('New device IDs:', newDevices.map(d => d.device_id || d.id || d.deviceId));
                
                displaySpaceDevices(newDevices);
                document.getElementById('spaceResourcesContainer').classList.remove('hidden');
                console.log('✅ Space resources display updated and shown');
                
                // Populate batch device IDs textbox with ALL space resources (not just new ones)
                addDeviceIdTextbox(resources, selectedSpaceId);
                
                // Auto-fetch raw Tuya Cloud API payload (LocalTuya-compatible format) and show in textbox
                fetch(`/api/cloud/spaces/${selectedSpaceId}/resources_raw`)
                    .then(r => r.json())
                    .then(data => {
                        const rawJson = document.getElementById('rawPayloadJson');
                        const rawStatus = document.getElementById('rawPayloadStatus');
                        if (rawJson) rawJson.value = JSON.stringify(data, null, 2);
                        if (rawStatus) rawStatus.innerText = data.error ? `Error: ${data.error}` : '✅ Raw payload loaded';
                        // Persist raw payload to localStorage
                        if (rawJson && !data.error) localStorage.setItem('tuyaGui_rawPayload', rawJson.value);
                    })
                    .catch(err => {
                        const rawJson = document.getElementById('rawPayloadJson');
                        const rawStatus = document.getElementById('rawPayloadStatus');
                        if (rawJson) rawJson.value = `Error: ${err.message}`;
                        if (rawStatus) rawStatus.innerText = 'Error fetching raw payload';
                    });
                
            } catch (error) {
                console.error('❌ Error loading space resources:', error);
                console.error('Error details:', error.stack || error.message);
                alert('Error loading space resources');
            }
        }

        function displaySpaceDevices(devices) {
            const container = document.getElementById('spaceDevicesList');
            container.innerHTML = '';
            
            if (devices.length === 0) {
                container.innerHTML = '<div class="no-new-devices">No new devices found in this space</div>';
                return;
            }
            
            devices.forEach(device => {
                // Use res_id as the device identifier from Tuya Cloud
                const deviceId = device.res_id || device.device_id || device.id || device.deviceId;
                const spaceId = device.space_id || selectedSpaceId;
                const deviceElement = document.createElement('div');
                deviceElement.className = 'device-item new-device';
                deviceElement.dataset.deviceId = deviceId;
                deviceElement.innerHTML = `
                    <div class="device-info">
                        <strong>${device.name || deviceId}</strong>
                        <small>
                            Resource Type: ${device.res_type !== undefined ? device.res_type : 'Unknown'}<br>
                            Space: ${spaceId}
                        </small>
                    </div>
                    <button class="config-device-btn" data-device-id="${deviceId}" data-space-id="${spaceId}">
                        Configure Device
                    </button>
                `;
                
                container.appendChild(deviceElement);
            });
            
            // Add event listeners to configure buttons
            document.querySelectorAll('.config-device-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const deviceId = e.target.dataset.deviceId;
                    const spaceId = e.target.dataset.spaceId;
                    configureNewDevice(deviceId, spaceId);
                });
            });
        }

        function addDeviceIdTextbox(devices, spaceId) {
            const batchSection = document.getElementById('batchDevicesSection');
            const textbox = document.getElementById('deviceIdsTextbox');
            const deviceList = document.getElementById('spaceDevicesList');
            const configureBtn = document.getElementById('configure-devices-btn');
            if (!batchSection || !textbox) return;

            const deviceIds = devices.map(d => d.res_id || d.device_id || d.id || d.deviceId).filter(Boolean);
            textbox.value = deviceIds.join(', ');
            localStorage.setItem('tuyaGui_deviceIds', deviceIds.join(', '));
            batchSection.classList.remove('hidden');

            // Hide individual device cards and configure button in batch mode
            if (deviceList) deviceList.classList.add('hidden');
            if (configureBtn) configureBtn.classList.add('hidden');

            // Wire up fetch button ("Get device IDs")
            const fetchBtn = document.getElementById('fetchDetailsBtn');
            if (fetchBtn) {
                fetchBtn.onclick = fetchDeviceDetailsFromList;
            }

            // Wire up copy button
            const copyBtn = document.getElementById('copyIdsBtn');
            if (copyBtn) {
                copyBtn.onclick = function() {
                    const tb = document.getElementById('deviceIdsTextbox');
                    if (!tb || !tb.value) return;
                    navigator.clipboard.writeText(tb.value).then(() => {
                        alert('Device IDs copied to clipboard!');
                    }).catch(() => {
                        tb.select();
                        document.execCommand('copy');
                        alert('Device IDs copied to clipboard!');
                    });
                };
            }

            // Wire up raw payload copy button
            const rawPayloadJson = document.getElementById('rawPayloadJson');
            const copyRawBtn = document.getElementById('copyRawPayloadBtn');
            if (copyRawBtn && rawPayloadJson) {
                copyRawBtn.onclick = function() {
                    if (!rawPayloadJson || !rawPayloadJson.value) return;
                    navigator.clipboard.writeText(rawPayloadJson.value).then(() => {
                        alert('Raw payload JSON copied to clipboard!');
                    }).catch(() => {
                        rawPayloadJson.select();
                        document.execCommand('copy');
                        alert('Raw payload JSON copied to clipboard!');
                    });
                };
            }

            // Wire up raw payload download button
            const downloadRawBtn = document.getElementById('downloadRawPayloadBtn');
            if (downloadRawBtn && rawPayloadJson) {
                downloadRawBtn.onclick = function() {
                    if (!rawPayloadJson || !rawPayloadJson.value) return;
                    const blob = new Blob([rawPayloadJson.value], {type: 'application/json'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `space_${spaceId}_resources_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                };
            }
        }

        function configureNewDevice(deviceId, spaceId) {
            // Fetch detailed info for this device and build LocalTuya configuration
            console.log(`Configuring device ${deviceId} from space ${spaceId}`);
            
            // Show loading state
            const btn = document.querySelector(`.config-device-btn[data-device-id="${deviceId}"]`);
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Fetching...';
            }
            
            fetch(`/api/device/${deviceId}/cloud_device_details`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error(`Error fetching device ${deviceId}:`, data.error);
                        alert(`Error fetching device details: ${data.error}`);
                        if (btn) {
                            btn.disabled = false;
                            btn.textContent = 'Configure Device';
                        }
                        return;
                    }
                    
                    const deviceInfo = data.device_info || {};
                    const functions = data.functions || {};
                    const factoryInfo = data.factory_info || {};
                    
                    // Build device config for LocalTuya
                    const deviceConfig = {
                        device_id: deviceId,
                        name: deviceInfo.name || deviceInfo.friendly_name || deviceId,
                        product_id: deviceInfo.product_id || '',
                        product_name: deviceInfo.product_name || '',
                        model: deviceInfo.model || '',
                        category: deviceInfo.category || '',
                        status: deviceInfo.status || {},
                        dps: {},
                        manufacturer: factoryInfo.manufacturer || '',
                        mac: factoryInfo.mac || deviceInfo.mac || deviceInfo.device_mac || '',
                        uuid: factoryInfo.uuid || deviceInfo.uuid || '',
                        local_key: deviceInfo.local_key || '',
                        space_id: spaceId,
                        source: 'space_management'
                    };
                    
                    // Process DP functions
                    for (const [dpId, func] of Object.entries(functions)) {
                        if (func && typeof func === 'object') {
                            deviceConfig.dps[dpId] = {
                                name: func.name || func.code || `DP${dpId}`,
                                type: func.type || 'string',
                                value: func.value || '',
                                access: func.access || func.accessMode || 'read_write',
                                values: func.values || {}
                            };
                        }
                    }
                    
                    // Create configuration document
                    const configDocument = {
                        version: "1.0",
                        source: "tuya_space_management",
                        space_id: spaceId,
                        exported_at: new Date().toISOString(),
                        devices: [deviceConfig]
                    };
                    
                    console.log('=== LOCALTUYA CONFIGURATION DOCUMENT ===');
                    console.log(JSON.stringify(configDocument, null, 2));
                    
                    // Show in modal
                    showConfigDocumentModal(configDocument, JSON.stringify(configDocument, null, 2), [
                        `=== Single Device Configuration ===`,
                        `Space ID: ${spaceId}`,
                        `Device ID: ${deviceId}`,
                        `Timestamp: ${new Date().toISOString()}`,
                        '',
                        `✓ ${deviceConfig.name} (${deviceId})`,
                        `  Product: ${deviceConfig.product_name} | Model: ${deviceConfig.model}`,
                        `  DPs: ${Object.keys(deviceConfig.dps).length}`,
                        ''
                    ]);
                    
                    if (btn) {
                        btn.disabled = false;
                        btn.textContent = 'Configure Device';
                    }
                })
                .catch(error => {
                    console.error(`Error processing device ${deviceId}:`, error);
                    alert(`Error processing device: ${error.message}`);
                    if (btn) {
                        btn.disabled = false;
                        btn.textContent = 'Configure Device';
                    }
                });
        }

        async function getExistingDevices() {
            // Get list of already configured devices from local configuration
            try {
                const response = await fetch('/api/devices');
                const data = await response.json();
                
                if (data.error) {
                    console.error('Error loading existing devices:', data.error);
                    return [];
                }
                
                // Extract device IDs from existing devices
                const existingDevices = [];
                if (data.devices) {
                    for (const [deviceId, deviceInfo] of Object.entries(data.devices)) {
                        if (deviceInfo && deviceInfo.device_id) {
                            existingDevices.push(deviceInfo.device_id);
                        } else {
                            existingDevices.push(deviceId);
                        }
                    }
                }
                
                return existingDevices;
            } catch (error) {
                console.error('Error loading existing devices:', error);
                return [];
            }
        }

        // Fetch detailed info for each new device and build LocalTuya JSON config
        async function fetchDeviceDetailsAndBuildConfig(devices, spaceId) {
            console.log('=== FETCHING DETAILED DEVICE INFO ===');
            console.log(`Fetching details for ${devices.length} device(s) from space ${spaceId}`);
            
            const configDevices = [];
            const logs = [`=== Space Management Device Configuration ===`, `Space ID: ${spaceId}`, `Timestamp: ${new Date().toISOString()}`, `Devices found: ${devices.length}`, ''];
            
            // Show progress modal
            showProgressModal(devices.length);
            
            for (let i = 0; i < devices.length; i++) {
                const device = devices[i];
                const deviceId = device.res_id || device.device_id || device.id || device.deviceId;
                if (!deviceId) {
                    console.warn('Skipping device with no ID:', device);
                    continue;
                }
                
                try {
                    console.log(`Fetching details for device: ${deviceId}`);
                    logs.push(`--- Fetching device: ${deviceId} ---`);
                    
                    // Update progress
                    updateProgressModal(i + 1, devices.length, deviceId);
                    
                    const response = await fetch(`/api/device/${deviceId}/cloud_device_details`);
                    const data = await response.json();
                    
                    if (data.error) {
                        console.error(`Error fetching device ${deviceId}:`, data.error);
                        logs.push(`ERROR: ${data.error}`);
                        continue;
                    }
                    
                    const deviceInfo = data.device_info || {};
                    const functions = data.functions || {};
                    const factoryInfo = data.factory_info || {};
                    
                    // Build device config for LocalTuya
                    const deviceConfig = {
                        device_id: deviceId,
                        name: deviceInfo.name || deviceInfo.friendly_name || device.name || deviceId,
                        product_id: deviceInfo.product_id || '',
                        product_name: deviceInfo.product_name || '',
                        model: deviceInfo.model || '',
                        category: deviceInfo.category || '',
                        status: deviceInfo.status || {},
                        dps: {},
                        manufacturer: factoryInfo.manufacturer || '',
                        mac: factoryInfo.mac || deviceInfo.mac || deviceInfo.device_mac || '',
                        uuid: factoryInfo.uuid || deviceInfo.uuid || '',
                        local_key: deviceInfo.local_key || '',
                        space_id: spaceId,
                        source: 'space_management'
                    };
                    
                    // Process DP functions
                    for (const [dpId, func] of Object.entries(functions)) {
                        if (func && typeof func === 'object') {
                            deviceConfig.dps[dpId] = {
                                name: func.name || func.code || `DP${dpId}`,
                                type: func.type || 'string',
                                value: func.value || '',
                                access: func.access || func.accessMode || 'read_write',
                                values: func.values || {}
                            };
                        }
                    }
                    
                    configDevices.push(deviceConfig);
                    logs.push(`✓ ${deviceConfig.name} (${deviceId})`);
                    logs.push(`  Product: ${deviceConfig.product_name} | Model: ${deviceConfig.model}`);
                    logs.push(`  DPs: ${Object.keys(deviceConfig.dps).length}`);
                    logs.push('');
                    
                } catch (error) {
                    console.error(`Error processing device ${deviceId}:`, error);
                    logs.push(`ERROR processing ${deviceId}: ${error.message}`);
                }
            }
            
            // Hide progress modal
            hideProgressModal();
            const configDocument = {
                version: "1.0",
                source: "tuya_space_management",
                space_id: spaceId,
                exported_at: new Date().toISOString(),
                devices: configDevices
            };
            
            // Output to console for copy-paste
            console.log('=== LOCALTUYA CONFIGURATION DOCUMENT ===');
            console.log(JSON.stringify(configDocument, null, 2));
            
            // Also create a copy-paste friendly version
            const jsonString = JSON.stringify(configDocument, null, 2);
            
            // Show in UI - create a modal with the JSON
            showConfigDocumentModal(configDocument, jsonString, logs);
            
            console.log('=== CONFIGURATION COMPLETE ===');
            console.log(`Total devices processed: ${configDevices.length}`);
            console.log('Copy the JSON from the modal or console for LocalTuya configuration');
            
            return configDocument;
        }

        // Show configuration document in a modal for copy/download
        function downloadCloudJson() {
            const textarea = document.getElementById('cloudJsonOutput');
            if (!textarea.value) return;
            const blob = new Blob([textarea.value], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tuya_device_${selectedCloudId || 'export'}_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }

        // Progress Modal Functions
        function showProgressModal(total) {
            const existingModal = document.getElementById('progressModal');
            if (existingModal) existingModal.remove();

            const modal = document.createElement('div');
            modal.id = 'progressModal';
            modal.className = 'overlay';
            modal.style.zIndex = '3000';
            modal.innerHTML = `
                <div style="background:white; max-width:500px; margin:10vh auto; padding:30px; border-radius:12px; position:relative; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
                    <h2 style="margin:0 0 20px 0; color:#2c3e50; text-align:center;">⏳ Fetching Device Details</h2>
                    <div style="margin-bottom:15px; font-size:14px; color:#666; text-align:center;">
                        <span id="progressCurrent">0</span> / <span id="progressTotal">${total}</span> devices
                    </div>
                    <div style="background:#ecf0f1; border-radius:8px; height:12px; overflow:hidden; margin-bottom:15px;">
                        <div id="progressBar" style="background:#3498db; height:100%; width:0%; border-radius:8px; transition:width 0.3s ease;"></div>
                    </div>
                    <div style="font-size:13px; color:#7f8c8d; text-align:center; min-height:20px;">
                        <span id="progressDevice">Starting...</span>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        function updateProgressModal(current, total, deviceId) {
            const percent = Math.round((current / total) * 100);
            document.getElementById('progressCurrent').textContent = current;
            document.getElementById('progressTotal').textContent = total;
            document.getElementById('progressBar').style.width = percent + '%';
            document.getElementById('progressDevice').textContent = `Fetching: ${deviceId} (${current}/${total})`;
        }

        function hideProgressModal() {
            const modal = document.getElementById('progressModal');
            if (modal) modal.remove();
        }

function showConfigDocumentModal(configDocument, jsonString, logs) {
            // Remove any existing modal
            const existingModal = document.getElementById('configDocumentModal');
            if (existingModal) existingModal.remove();

            const modal = document.createElement('div');
            modal.id = 'configDocumentModal';
            modal.className = 'overlay';
            modal.style.zIndex = '2000';
            modal.innerHTML = `
                <div style="background:white; max-width:1200px; max-height:95vh; margin:1vh auto; padding:25px; border-radius:12px; position:relative; display:flex; flex-direction:column; overflow:hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                    <button onclick="closeConfigModal()" style="position:absolute; top:15px; right:20px; background:none; border:none; font-size:28px; cursor:pointer; color:#333; z-index:10; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; transition:background 0.2s;">&times;</button>
                    <h2 style="margin:0 0 15px 0; color:#2c3e50;">📋 LocalTuya Configuration Document</h2>
                    <div style="margin-bottom:20px; padding:15px; background:#f8f9fa; border-radius:8px; font-size:13px; color:#666;">
                        <strong>Space ID:</strong> ${configDocument.space_id} | 
                        <strong>Devices:</strong> ${configDocument.devices.length} | 
                        <strong>Exported:</strong> ${configDocument.exported_at}
                    </div>
                    
                    <div style="display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;">
                        <button class="primary-btn" onclick="copyConfigJson()" style="padding:10px 20px; font-size:13px;">📋 Copy JSON</button>
                        <button class="btn-send" onclick="downloadConfigJson()" style="padding:10px 20px; font-size:13px;">💾 Download JSON</button>
                        <button class="btn-cloud" onclick="copyConfigMinified()" style="padding:10px 20px; font-size:13px;">📄 Copy Minified</button>
                    </div>

                    <div style="display:flex; gap:15px; flex:1; overflow:hidden;">
                        <!-- JSON Panel -->
                        <div style="flex:1; display:flex; flex-direction:column; min-width:0;">
                            <label style="font-size:12px; font-weight:bold; color:#666; margin-bottom:8px;">Full JSON (Pretty):</label>
                            <textarea id="configJsonPretty" readonly style="flex:1; font-family:'Monaco','Menlo','Ubuntu Mono',monospace; font-size:12px; padding:15px; border:1px solid #ddd; border-radius:6px; background:#fafafa; color:#333; resize:none; overflow:auto; line-height:1.4;"></textarea>
                        </div>
                        
                        <!-- Logs Panel -->
                        <div style="width:400px; display:flex; flex-direction:column; min-width:0; flex-shrink:0;">
                            <label style="font-size:12px; font-weight:bold; color:#666; margin-bottom:8px;">Configuration Log:</label>
                            <textarea id="configLogs" readonly style="flex:1; font-family:'Monaco','Menlo','Ubuntu Mono',monospace; font-size:11px; padding:12px; border:1px solid #ddd; border-radius:6px; background:#1e1e1e; color:#00ff00; resize:none; overflow:auto; line-height:1.3;"></textarea>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Populate content
            document.getElementById('configJsonPretty').value = JSON.stringify(configDocument, null, 2);
            document.getElementById('configLogs').value = logs.join('\\n');
            
            // Auto-scroll logs to bottom
            const logsEl = document.getElementById('configLogs');
            logsEl.scrollTop = logsEl.scrollHeight;
        }

        function closeConfigModal() {
            const modal = document.getElementById('configDocumentModal');
            if (modal) modal.remove();
        }

        function copyConfigJson() {
            const textarea = document.getElementById('configJsonPretty');
            if (!textarea.value) return;
            navigator.clipboard.writeText(textarea.value).then(() => {
                alert('Full JSON copied to clipboard!');
            }).catch(() => {
                textarea.select();
                document.execCommand('copy');
                alert('Full JSON copied to clipboard!');
            });
        }

        function copyConfigMinified() {
            const textarea = document.getElementById('configJsonPretty');
            if (!textarea.value) return;
            const minified = JSON.stringify(JSON.parse(textarea.value));
            navigator.clipboard.writeText(minified).then(() => {
                alert('Minified JSON copied to clipboard!');
            }).catch(() => {
                alert('Failed to copy minified JSON');
            });
        }

        function downloadConfigJson() {
            const textarea = document.getElementById('configJsonPretty');
            if (!textarea.value) return;
            const blob = new Blob([textarea.value], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tuya_space_config_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }

        async function selectCloud(devId) {
            selectedCloudId = devId;
            document.querySelectorAll('#cloudList .item').forEach(el => el.classList.remove('active'));
            document.getElementById('cloudDetails').style.display = 'flex';
            const d = cloudDevices[devId] || {};
            document.getElementById('cloudName').innerText = d.friendly_name || d.name || devId;
            document.getElementById('cloudMeta').innerText = `ID: ${devId} | Category: ${d.category || '-'} | Product: ${d.product_name || '-'} | Local IP: ${d.local_ip || d.host || 'N/A'} | Cloud IP: ${d.cloud_ip || d.ip || 'N/A'} | MAC: ${d.match_mac || d.mac || d.device_mac || 'N/A'}`;
            const overlay = document.getElementById('cloudLoadingOverlay');
            const logs = document.getElementById('cloudLogs');
            overlay.classList.remove('hidden');
            logs.innerText = 'Loading device details...';
            try {
                const r = await fetch(`/api/device/${devId}/cloud_device_details`);
                const data = await r.json();
                logs.innerText = data.tech_logs || '';
                if (data.error) {
                    document.getElementById('cloudDetailBody').innerHTML = `<tr><td colspan="2">Error: ${data.error}</td></tr>`;
                    document.getElementById('cloudJsonOutput').value = '';
                    return;
                }
                const funcs = data.functions || {};
                const devInfo = data.device_info || {};
                const factoryInfo = data.factory_info || {};
                const rows = Object.keys(funcs).sort().map(dpId => {
                    const info = funcs[dpId] || {};
                    const vals = info.values ? JSON.stringify(info.values) : '-';
                    return `<tr>
                        <td><b>${dpId}</b></td>
                        <td>${info.name || '-'}</td>
                    </tr>`;
                });
                document.getElementById('cloudDetailBody').innerHTML = rows.length ? rows.join('') : '<tr><td colspan="2">No functions returned.</td></tr>';
                
                // Prepare full JSON for export
                const fullJson = {
                    result: {
                        active_time: devInfo.active_time,
                        bind_space_id: devInfo.bind_space_id,
                        category: devInfo.category,
                        create_time: devInfo.create_time,
                        custom_name: devInfo.custom_name || "",
                        icon: devInfo.icon,
                        id: devId,
                        ip: devInfo.ip || devInfo.cloud_ip || devInfo.local_ip,
                        is_online: devInfo.is_online || devInfo.online,
                        lat: devInfo.lat,
                        local_key: devInfo.local_key,
                        lon: devInfo.lon,
                        model: devInfo.model,
                        name: devInfo.name || devInfo.friendly_name,
                        product_id: devInfo.product_id,
                        product_name: devInfo.product_name,
                        sub: devInfo.sub,
                        time_zone: devInfo.time_zone,
                        update_time: devInfo.update_time,
                        uuid: devInfo.uuid,
                        functions: funcs
                    },
                    success: true,
                    t: Date.now(),
                    tid: "tuya_gui_export_" + devId
                };
                document.getElementById('cloudJsonOutput').value = JSON.stringify(fullJson, null, 2);
            } catch(e) {
                document.getElementById('cloudDetailBody').innerHTML = `<tr><td colspan="2">Error: ${e}</td></tr>`;
                document.getElementById('cloudJsonOutput').value = '';
            } finally {
                overlay.classList.add('hidden');
            }
        }

        function filterCloudDevices() {
            const input = document.getElementById('cloudSearch');
            const filter = input.value.toLowerCase();
            const items = document.querySelectorAll('#cloudList .item');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(filter) ? '' : 'none';
            });
        }

        function copyCloudJson() {
            const textarea = document.getElementById('cloudJsonOutput');
            if (!textarea.value) return;
            navigator.clipboard.writeText(textarea.value).then(() => {
                alert('JSON copied to clipboard!');
            }).catch(() => {
                textarea.select();
                document.execCommand('copy');
                alert('JSON copied to clipboard!');
            });
        }

        function downloadCloudJson() {
            const textarea = document.getElementById('cloudJsonOutput');
            if (!textarea.value) return;
            const blob = new Blob([textarea.value], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tuya_device_${selectedCloudId || 'export'}_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }

        // Batch fetch device details from CSV list and show combined LocalTuya config
        async function fetchDeviceDetailsFromList() {
            const textarea = document.getElementById('deviceIdsTextbox');
            const btn = document.getElementById('fetchDetailsBtn');
            const statusDiv = document.getElementById('batchStatus');

            if (!textarea || !textarea.value.trim()) {
                alert('Please enter device IDs');
                return;
            }

            const deviceIds = textarea.value.split(',').map(id => id.trim()).filter(id => id);
            if (deviceIds.length === 0) {
                alert('No valid device IDs found');
                return;
            }

            if (btn) { btn.disabled = true; btn.textContent = '⏳ Fetching...'; }
            if (statusDiv) { statusDiv.innerText = `Fetching ${deviceIds.length} device(s)...`; }

            const configDevices = [];
            const logs = [`=== Batch Device Details ===`, `Devices requested: ${deviceIds.length}`, `Timestamp: ${new Date().toISOString()}`, ''];

            for (let i = 0; i < deviceIds.length; i++) {
                const devId = deviceIds[i];
                if (statusDiv) { statusDiv.innerText = `Fetching device ${i + 1}/${deviceIds.length}: ${devId}...`; }

                try {
                    const resp = await fetch(`/api/device/${devId}/cloud_device_details`);
                    const data = await resp.json();

                    if (data.error) {
                        console.error(`Error fetching device ${devId}:`, data.error);
                        logs.push(`✗ ${devId}: ${data.error}`);
                        continue;
                    }

                    const devInfo = data.device_info || {};
                    const funcs = data.functions || {};
                    const factoryInfo = data.factory_info || {};

                    // Tuya Cloud API-compatible device format (LocalTuya import expects result[])
                    const tuyaDevice = {
                        id: devId,
                        name: devInfo.name || devInfo.friendly_name || devId,
                        local_key: devInfo.local_key || '',
                        ip: devInfo.local_ip || devInfo.ip || '',
                        product_id: devInfo.product_id || devInfo.product_key || '',
                        product_name: devInfo.product_name || '',
                        category: devInfo.category || '',
                        model: devInfo.model || '',
                        status: devInfo.status || {},
                        firmware_version: devInfo.firmware_version || '',
                        manufacturer: factoryInfo.manufacturer || '',
                        mac: factoryInfo.mac || devInfo.mac || devInfo.device_mac || '',
                        uuid: factoryInfo.uuid || devInfo.uuid || '',
                        create_date: devInfo.create_date || '',
                        update_date: devInfo.update_date || '',
                        active_time: devInfo.active_time || '',
                        icon: devInfo.icon || '',
                        comment: devInfo.comment || ''
                    };

                    configDevices.push(tuyaDevice);
                    logs.push(`✓ ${devId}: ${tuyaDevice.name}`);
                } catch (err) {
                    console.error(`Error fetching device ${devId}:`, err);
                    logs.push(`✗ ${devId}: ${err.message}`);
                }
            }

            if (btn) { btn.disabled = false; btn.textContent = 'Get device IDs'; }
            if (statusDiv) { statusDiv.innerText = `Done: ${configDevices.length}/${deviceIds.length} devices fetched`; }

            if (configDevices.length === 0) {
                alert('No device details could be retrieved');
                return;
            }

            const jsonStr = JSON.stringify({ result: configDevices }, null, 2);

            // Populate result textbox
            const resultJson = document.getElementById('batchResultJson');
            const resultSection = document.getElementById('batchResultSection');
            if (resultJson) resultJson.value = jsonStr;
            if (resultSection) resultSection.classList.remove('hidden');
            // Persist batch result to localStorage
            if (resultJson) localStorage.setItem('tuyaGui_batchResult', resultJson.value);

            // Wire up result copy button
            const copyResultBtn = document.getElementById('copyBatchJsonBtn');
            if (copyResultBtn) {
                copyResultBtn.onclick = function() {
                    if (!resultJson || !resultJson.value) return;
                    navigator.clipboard.writeText(resultJson.value).then(() => {
                        alert('JSON copied to clipboard!');
                    }).catch(() => {
                        resultJson.select();
                        document.execCommand('copy');
                        alert('JSON copied to clipboard!');
                    });
                };
            }

            // Wire up result download button
            const downloadResultBtn = document.getElementById('downloadBatchJsonBtn');
            if (downloadResultBtn) {
                downloadResultBtn.onclick = function() {
                    if (!resultJson || !resultJson.value) return;
                    const blob = new Blob([resultJson.value], {type: 'application/json'});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `tuya_batch_devices_${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                };
            }

            alert(`✅ Fetched ${configDevices.length}/${deviceIds.length} device(s). JSON ready in the result box below.`);
        }

        init();
    </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, version=VERSION)


@app.route("/api/settings", methods=["GET", "POST"])
def settings():
    s = load_settings()
    if request.method == "POST":
        s.update(request.json)
        save_settings(s)
    return jsonify(s)


@app.route("/api/devices")
def api_devices():
    _log.info("GET /api/devices — start")
    t0 = time.monotonic()
    devices = get_devices_data()
    _log.info("GET /api/devices — local devices: %d", len(devices))

    if TuyaCloudApi is None:
        _log.warning("GET /api/devices — TuyaCloudApi not available, returning local only")
        return jsonify({"devices": devices, "usage": load_settings()["usage"]})

    cloud_conf = _build_cloud_conf()
    if not cloud_conf:
        _log.warning("GET /api/devices — no cloud config found, returning local only")
        return jsonify({"devices": devices, "usage": load_settings()["usage"]})

    _log.info("GET /api/devices — cloud config OK (region=%s), starting async fetch", cloud_conf.get("region"))

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            _log.debug("api_devices._run: calling _fetch_cloud_devices with 20s timeout")
            cloud_devices = await asyncio.wait_for(_fetch_cloud_devices(cloud_conf), timeout=20)

            _log.info("api_devices._run: cloud returned %d devices", len(cloud_devices))

            cloud_by_mac: dict = {}
            cloud_by_id: dict = {}
            for dev_id, info in (cloud_devices or {}).items():
                if not isinstance(info, dict):
                    continue
                mac = _extract_mac(info.get("mac") or info.get("device_mac"))
                if mac:
                    cloud_by_mac[mac] = info
                cloud_by_id[dev_id] = info

            enriched: dict = {}
            for dev_id, d in (devices or {}).items():
                d = dict(d)
                local_ip = d.get("host")
                mac = _extract_mac(d.get("mac"))

                cloud = None
                if mac and mac in cloud_by_mac:
                    cloud = cloud_by_mac.get(mac)
                if cloud is None:
                    cloud = (
                        cloud_by_id.get(d.get("device_id"))
                        or cloud_by_id.get(d.get("gwId"))
                        or cloud_by_id.get(dev_id)
                    )

                cloud_ip = None
                cloud_mac = None
                if isinstance(cloud, dict):
                    cloud_ip = cloud.get("ip") or cloud.get("local_ip")
                    cloud_mac = _extract_mac(cloud.get("mac") or cloud.get("device_mac"))
                    d.setdefault("category", cloud.get("category"))
                    d.setdefault("product_name", cloud.get("product_name"))

                resolved_mac = _extract_mac(d.get("mac") or d.get("match_mac")) or cloud_mac
                if not resolved_mac:
                    resolved_mac = _lan_mac_for_ip(local_ip)

                d["local_ip"] = local_ip
                d["cloud_ip"] = cloud_ip
                d["match_mac"] = resolved_mac
                enriched[dev_id] = d

            _log.info("api_devices._run: enriched %d devices", len(enriched))
            return {
                "devices": enriched,
                "usage": load_settings()["usage"],
                "tech_logs": "\\n".join(h.records),
            }
        except asyncio.TimeoutError:
            _log.error("api_devices._run: _fetch_cloud_devices timed out after 20s — Tuya Cloud unreachable or credentials wrong")
            return {
                "devices": devices,
                "usage": load_settings()["usage"],
                "error": "Tuya Cloud API timed out (20s). Check credentials and network.",
                "tech_logs": "\\n".join(h.records),
            }
        except Exception as e:
            _log.error("api_devices._run: exception: %s", e, exc_info=True)
            return {
                "devices": devices,
                "usage": load_settings()["usage"],
                "error": str(e),
                "tech_logs": "\\n".join(h.records),
            }
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        result = future.result(timeout=25)
        elapsed = time.monotonic() - t0
        _log.info("GET /api/devices — done in %.2fs, error=%s", elapsed, result.get("error"))
        return jsonify(result)
    except Exception as e:
        elapsed = time.monotonic() - t0
        _log.error("GET /api/devices — future.result failed after %.2fs: %s", elapsed, e)
        return jsonify({"devices": devices, "usage": load_settings()["usage"], "error": str(e)})


@app.route("/api/devices/unadded")
def api_unadded_devices():
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    configured_devices = get_devices_data()
    configured_ids = set((configured_devices or {}).keys())
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            devs = await api.async_get_devices_list(force_update=True)
            cloud_devices: dict = {}
            if isinstance(devs, dict):
                cloud_devices = devs
            elif isinstance(getattr(api, "device_list", None), dict):
                cloud_devices = api.device_list
            elif isinstance(getattr(api, "devices", None), dict):
                cloud_devices = api.devices

            configured_by_mac: dict = {}
            configured_by_device_id: dict = {}
            for d in (configured_devices or {}).values():
                if not isinstance(d, dict):
                    continue
                m = _extract_mac(d.get("mac") or d.get("match_mac"))
                if m:
                    configured_by_mac[m] = d.get("host")
                if d.get("device_id"):
                    configured_by_device_id[d.get("device_id")] = d.get("host")
                if d.get("gwId"):
                    configured_by_device_id[d.get("gwId")] = d.get("host")

            unadded: dict = {}
            for dev_id, info in cloud_devices.items():
                if dev_id in configured_ids:
                    continue
                ip_cloud = info.get("ip") or info.get("local_ip") or ""
                mac = _extract_mac(info.get("mac") or info.get("device_mac"))

                if mac and mac in configured_by_mac:
                    continue
                if dev_id in configured_by_device_id:
                    continue
                if (
                    isinstance(info, dict)
                    and info.get("gwId")
                    and info.get("gwId") in configured_by_device_id
                ):
                    continue

                local_ip = configured_by_mac.get(mac) if mac else None
                local_ip = local_ip or configured_by_device_id.get(dev_id)
                info["cloud_ip"] = ip_cloud
                info["local_ip"] = local_ip
                info["match_mac"] = mac
                unadded[dev_id] = info
            return {"devices": unadded, "tech_logs": "\\n".join(h.records)}
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=25))
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/devices/cloud")
def api_cloud_devices():
    """Return all devices from Tuya Cloud with full details."""
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            devs = await api.async_get_devices_list(force_update=True)
            cloud_devices: dict = {}
            if isinstance(devs, dict):
                cloud_devices = devs
            elif isinstance(getattr(api, "device_list", None), dict):
                cloud_devices = api.device_list
            elif isinstance(getattr(api, "devices", None), dict):
                cloud_devices = api.devices

            # Also try to get functions for each device (in parallel)
            # But limit to avoid timeout - we'll return raw cloud data and let frontend fetch details on demand
            # We can enrich with local MAC/IP info if available
            configured_devices = get_devices_data()
            configured_by_mac: dict = {}
            configured_by_device_id: dict = {}
            for d in (configured_devices or {}).values():
                if not isinstance(d, dict):
                    continue
                m = _extract_mac(d.get("mac") or d.get("match_mac"))
                if m:
                    configured_by_mac[m] = d.get("host")
                if d.get("device_id"):
                    configured_by_device_id[d.get("device_id")] = d.get("host")
                if d.get("gwId"):
                    configured_by_device_id[d.get("gwId")] = d.get("host")

            enriched: dict = {}
            for dev_id, info in cloud_devices.items():
                if not isinstance(info, dict):
                    continue
                ip_cloud = info.get("ip") or info.get("local_ip") or ""
                mac = _extract_mac(info.get("mac") or info.get("device_mac"))
                
                local_ip = configured_by_mac.get(mac) if mac else None
                local_ip = local_ip or configured_by_device_id.get(dev_id)
                
                info["cloud_ip"] = ip_cloud
                info["local_ip"] = local_ip
                info["match_mac"] = mac
                enriched[dev_id] = info
            
            return {"devices": enriched, "tech_logs": "\\n".join(h.records)}
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=25))
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/device/discover_by_ip", methods=["POST"])
def api_discover_by_ip():
    """Discover a Tuya device at a specific IP address by attempting local connection."""
    if connect is None:
        return jsonify({"error": "LocalTuya core dependencies unavailable"}), 503
    
    data = request.json or {}
    target_ip = data.get("ip", "").strip()
    if not target_ip:
        return jsonify({"error": "IP address required"}), 400
    
    async def _run():
        h = ListHandler()
        from pytuya import _LOGGER as pytuya_log
        pytuya_log.setLevel(logging.DEBUG)
        pytuya_log.addHandler(h)
        pytuya_log.propagate = True
        
        try:
            h.records.append(f"[discover] Scanning {target_ip}...")
            
            for port in [6668, 6666, 6667]:
                try:
                    h.records.append(f"[discover] Trying {target_ip}:{port}...")
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((target_ip, port))
                    sock.close()
                    
                    if result == 0:
                        h.records.append(f"[discover] ✓ Device responding on {target_ip}:{port}")
                        
                        # Ottieni MAC via ARP
                        mac = _lan_mac_for_ip(target_ip)
                        if mac:
                            h.records.append(f"[discover] MAC address from ARP: {mac}")
                        
                        # 1) Prova a cercare nel cloud
                        ha_config = get_ha_config()
                        cloud_conf = None
                        for entry in ha_config.get("data", {}).get("entries", []):
                            if entry.get("domain") == "localtuya":
                                cloud_conf = entry.get("data")
                                break
                        
                        cloud_device = None
                        cloud_device_id = None
                        if cloud_conf and TuyaCloudApi is not None:
                            try:
                                h.records.append("[discover] Querying cloud API for device details...")
                                api = TuyaCloudApi(
                                    cloud_conf["region"],
                                    cloud_conf["client_id"],
                                    cloud_conf["client_secret"],
                                    cloud_conf["user_id"],
                                )
                                await api.async_connect()
                                cloud_devs = await api.async_get_devices_list(force_update=True)
                                
                                # Debug: stampa tipo e primi elementi
                                h.records.append(f"[discover] Cloud devices type: {type(cloud_devs)}")
                                if isinstance(cloud_devs, dict):
                                    sample = list(cloud_devs.items())[:2]
                                    h.records.append(f"[discover] Cloud devices sample: {sample}")
                                    # Cerca per IP o MAC
                                    for dev_id, dev_info in cloud_devs.items():
                                        if not isinstance(dev_info, dict):
                                            continue
                                        dev_ip = dev_info.get("local_ip") or dev_info.get("ip") or ""
                                        dev_mac = _extract_mac(dev_info.get("mac") or dev_info.get("device_mac"))
                                        if dev_ip == target_ip or (mac and dev_mac == mac):
                                            cloud_device = dev_info
                                            cloud_device_id = dev_id
                                            h.records.append(f"[discover] Found cloud device: {dev_id} (IP match={dev_ip==target_ip}, MAC match={dev_mac==mac})")
                                            break
                                else:
                                    h.records.append(f"[discover] Cloud devices is not a dict: {cloud_devs}")
                            except Exception as e:
                                h.records.append(f"[discover] Cloud API error: {e}")
                                import traceback
                                h.records.append(traceback.format_exc())
                        
                        # 2) Se non trovato nel cloud, cerca nella configurazione locale di localtuya
                        local_device = None
                        local_device_id = None
                        devices_local = get_devices_data()  # dict {dev_id: config}
                        for dev_id, dev_cfg in devices_local.items():
                            if dev_cfg.get("host") == target_ip:
                                local_device = dev_cfg
                                local_device_id = dev_id
                                h.records.append(f"[discover] Found device in local configuration: {dev_id}")
                                break
                        
                        # Prepara la risposta
                        if cloud_device:
                            cloud_device["local_ip"] = target_ip
                            cloud_device["port"] = port
                            cloud_device["status"] = "discovered_from_cloud"
                            # Aggiungi anche la local_key se presente
                            return {
                                "device": cloud_device,
                                "device_id": cloud_device_id,
                                "tech_logs": "\\n".join(h.records)
                            }
                        elif local_device:
                            local_device["status"] = "discovered_from_local_config"
                            local_device["port"] = port
                            local_device["match_mac"] = mac
                            return {
                                "device": local_device,
                                "device_id": local_device_id,
                                "tech_logs": "\\n".join(h.records)
                            }
                        else:
                            # Restituisci solo le info di base, chiedendo all'utente di inserire ID e chiave
                            return {
                                "device": {
                                    "ip": target_ip,
                                    "port": port,
                                    "mac": mac,
                                    "status": "needs_manual_config",
                                    "note": "Device responds but not found in cloud or local config. Please provide device_id and local_key manually (obtain from Tuya IoT app or cloud)."
                                },
                                "tech_logs": "\\n".join(h.records)
                            }
                except Exception as e:
                    h.records.append(f"[discover] Port {port} error: {e}")
                    continue
            
            return {
                "error": f"No response from {target_ip} on common Tuya ports",
                "tech_logs": "\\n".join(h.records)
            }
        except Exception as e:
            h.records.append(f"[discover] Fatal error: {e}")
            return {
                "error": str(e),
                "tech_logs": "\\n".join(h.records)
            }
        finally:
            pytuya_log.removeHandler(h)
    
    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=30))
    except Exception as e:
        return jsonify({"error": str(e), "tech_logs": ""})

# ---------------------------------------------------------------------------
# /api/device/discover_by_ip_advanced — Strategy 3x3 (Active, Cmd 16, Push-wait)
# ---------------------------------------------------------------------------
@app.route("/api/device/discover_by_ip_advanced", methods=["POST"])
def api_discover_by_ip_advanced():
    if connect is None: return jsonify({"error": "Dependencies missing"}), 503
    data = request.json or {}
    target_ip = data.get("ip", "").strip()
    if not target_ip: return jsonify({"error": "IP address required"}), 400

    async def _run():
        h = ListHandler()
        from pytuya import _LOGGER as pytuya_log
        pytuya_log.setLevel(logging.DEBUG)
        pytuya_log.addHandler(h)

        def _log(msg):
            h.records.append(msg)
            print(f"[DISCOVER-ADV] {msg}")

        def _filter_numeric(dps_dict: dict) -> dict:
            return {int(k): v for k, v in dps_dict.items() if (isinstance(k, int) or (isinstance(k, str) and k.isdigit()))}

        def _extract_dps(res, proto=None) -> dict:
            if not res and proto:
                # Ispeziona cache interne se la risposta diretta è vuota
                for attr in ('dps', '_dps', 'dps_cache', '_dps_cache', 'status_cache'):
                    val = getattr(proto, attr, None)
                    if isinstance(val, dict) and val:
                        if isinstance(val.get("parent"), dict):
                            f = _filter_numeric(val["parent"])
                            if f:
                                _log(f"✓ Found DPS in internal proto.{attr}['parent']")
                                return f
                        f = _filter_numeric(val)
                        if f: 
                            _log(f"✓ Found DPS in internal proto.{attr}")
                            return f
                        for cache_key, cache_val in val.items():
                            if isinstance(cache_val, dict):
                                f = _filter_numeric(cache_val)
                                if f:
                                    _log(f"✓ Found DPS in internal proto.{attr}[{cache_key!r}]")
                                    return f
            if isinstance(res, dict):
                if isinstance(res.get("dps"), dict):
                    d = res["dps"]
                elif isinstance(res.get("parent"), dict):
                    d = res["parent"]
                else:
                    d = res
                return _filter_numeric(d)
            return {}

        # Listener per catturare i push asincroni
        class ScanListener(TuyaListener):
            def __init__(self):
                self.future = asyncio.get_running_loop().create_future()
            def status_updated(self, status):
                _log(f"PUSH RECEIVED via Listener: {repr(status)[:100]}")
                if not self.future.done():
                    self.future.set_result(status)
            def disconnected(self, exc=""): 
                _log(f"Listener disconnected: {exc}")
            def subdevice_state_updated(self, state): pass

        try:
            _log(f"Starting ADVANCED scan for {target_ip}...")
            # ... rest of the code ...
            mac = _lan_mac_for_ip(target_ip)
            cloud_conf = _build_cloud_conf()
            cloud_device = None
            
            if cloud_conf:
                _log("Querying cloud API...")
                cloud_devs = await _fetch_cloud_devices(cloud_conf)
                known_id = "bf0e2041fb7f7875c4bcss"
                if target_ip == "192.168.0.28" and known_id in cloud_devs:
                    cloud_device = cloud_devs[known_id]
                    _log(f"Cloud Match: Known Smart Meter ID {known_id}")
                else:
                    for d_id, d_info in cloud_devs.items():
                        if _extract_mac(d_info.get("mac")) == mac:
                            cloud_device = d_info
                            _log(f"Cloud Match: {d_id} by MAC")
                            break

            local_key = cloud_device.get("local_key") if cloud_device else None
            dev_id = cloud_device.get("id") if cloud_device else (known_id if target_ip == "192.168.0.28" else None)

            local_status = None
            cloud_status = {}
            cloud_display_status = {}
            cloud_display_units = {}
            local_error_type = None
            local_note = f"Cloud Key found: {'YES' if local_key else 'NO'}"
            if local_key and dev_id:
                for ver in [3.4, 3.3, 3.1]:
                    _log(f"--- Strategy Attempt (Protocol v{ver}) ---")
                    proto = None
                    listener = ScanListener()
                    try:
                        # Corretta firma: connect(address, device_id, local_key, protocol_version, enable_debug, listener=None, port=6668, timeout=TIMEOUT_CONNECT)
                        proto = await asyncio.wait_for(
                            connect(target_ip, dev_id, local_key, ver, True, listener=listener), 
                            15
                        )
                        if ver == 3.4:
                            _log("✓ Protocol v3.4 session established")
                        
                        # A) detect_available_dps (cmd 16)
                        _log("A) Sending CMD 16 (Detect DPs)...")
                        try:
                            # Alcuni device v3.4 richiedono CMD 16 per iniziare a spingere dati
                            await asyncio.wait_for(proto.detect_available_dps(), 8)
                        except: pass
                        local_status = _extract_dps(None, proto)
                        
                        # B) Active status query
                        if not local_status:
                            _log("B) Sending active status query...")
                            try:
                                res = await asyncio.wait_for(proto.status(), 8)
                                local_status = _extract_dps(res, proto)
                            except Exception as e:
                                _log(f"Active status query error: {e}")

                        if not local_status and ver == 3.4:
                            local_error_type = "local_query_rejected"
                            local_note = (
                                "Protocol v3.4 session established, but the device did not "
                                "return local DPS. DP_QUERY_NEW is being rejected (retcode=1 "
                                "in pytuya logs) or the socket is closed by the device."
                            )
                            _log("Local v3.4 session works, but active status DPS are not available locally.")
                            _log("Skipping push-wait and legacy 3.3/3.1 attempts; use the Cloud/HA fallback for state.")
                            break
                        
                        # C) Push-wait (v3.4 only)
                        if not local_status and ver == 3.4:
                            _log("C) Push-wait mode enabled. Waiting for asynchronous data (max 60s)...")
                            try:
                                # Ciclo di heartbeat ogni 15s per sollecitare il push
                                for i in range(4):
                                    if listener.future.done(): break
                                    _log(f"Soliciting push via heartbeat {i+1}/4...")
                                    try: await proto.heartbeat()
                                    except: pass
                                    try:
                                        pushed = await asyncio.wait_for(asyncio.shield(listener.future), 15)
                                        local_status = _extract_dps(pushed, proto)
                                        if local_status: break
                                    except asyncio.TimeoutError: continue
                            except Exception as push_err:
                                _log(f"Push-wait error: {push_err}")

                        # D) Strategy D: Pure Listening (v3.4 only, no active queries at all)
                        if not local_status and ver == 3.4:
                            _log("D) Strategy D: Pure Listening (max 60s)...")
                            if hasattr(proto, 'transport') and proto.transport:
                                proto.transport.close()
                            await asyncio.sleep(3)
                            
                            listener = ScanListener()
                            try:
                                # Nuova connessione pulita
                                proto = await asyncio.wait_for(
                                    connect(target_ip, dev_id, local_key, ver, True, listener=listener), 
                                    15
                                )
                                # Aspettiamo senza bombardare di query, solo heartbeat ogni 25s
                                for i in range(2):
                                    if listener.future.done(): break
                                    _log(f"Passive wait cycle {i+1}/2 (Long wait, heartbeat every 25s)...")
                                    try:
                                        pushed = await asyncio.wait_for(asyncio.shield(listener.future), 25)
                                        local_status = _extract_dps(pushed, proto)
                                        if local_status: break
                                    except asyncio.TimeoutError:
                                        _log("No push in this cycle, sending heartbeat...")
                                        try: await proto.heartbeat()
                                        except: pass
                                        continue
                            except Exception as d_err:
                                _log(f"Strategy D connection failed: {d_err}")
                        
                        if local_status:
                            _log(f"✓ SUCCESS! Data: {local_status}")
                            break
                        if ver == 3.4:
                            local_error_type = "local_query_rejected"
                            local_note = (
                                "Protocol v3.4 session established, but the device did not "
                                "return local DPS. DP_QUERY_NEW is being rejected (retcode=1 "
                                "in pytuya logs) or the socket is closed by the device."
                            )
                            _log("Local v3.4 session works, but status DPS are not available locally; skipping legacy 3.3/3.1 attempts.")
                            break
                    except BaseException as e:
                        _log(f"v{ver} attempt failed: {type(e).__name__}: {e}")
                    finally:
                        if proto and hasattr(proto, 'transport') and proto.transport:
                            proto.transport.close()

            if dev_id:
                cloud_cfg = get_devices_data().get(dev_id, {"device_id": dev_id, "gwId": dev_id})
                cloud_status = await _cloud_status_as_dps(dev_id, cloud_cfg)
                if cloud_status:
                    funcs = await _get_cloud_functions_cached(dev_id, cloud_cfg)
                    cloud_display_status, cloud_display_units = _display_status_from_model(cloud_status, cloud_cfg, funcs)
                    _log(f"Cloud fallback status available: {len(cloud_status)} DPS")

            return {
                "device": {
                    "ip": target_ip, "id": dev_id, "mac": mac, 
                    "local_test_status": local_status,
                    "cloud_test_status": cloud_status,
                    "cloud_display_status": cloud_display_status,
                    "cloud_display_units": cloud_display_units,
                    "local_error_type": local_error_type,
                    "note": local_note
                },
                "tech_logs": "\\n".join(h.records)
            }
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            pytuya_log.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        # Aumentato a 180 secondi per coprire l'intera durata del test (C + D)
        return jsonify(future.result(timeout=180))
    except Exception as e:
        _log.error("Advanced discovery request timed out or failed: %s", e)
        return jsonify({
            "error": "Timeout or server error during advanced scan. Check terminal for background logs.",
            "device": {"ip": target_ip, "id": "timeout"},
            "tech_logs": "Scan exceeded 180 seconds. Check terminal for results."
        }), 504

# ---------------------------------------------------------------------------
# /api/device/<dev_id>/status  — uses connection pool + classified errors
# ---------------------------------------------------------------------------
@app.route("/api/device/<dev_id>/status")
def api_status(dev_id: str):
    if connect is None:
        return jsonify({"error": "LocalTuya core dependencies unavailable"}), 503
    devices = get_devices_data()
    d = devices.get(dev_id)
    if not d:
        return jsonify({"error": "Unknown device"}), 404
    t = int(request.args.get("timeout", 10))

    async def _run():
        from pytuya import _LOGGER as pytuya_log

        h = ListHandler()
        pytuya_log.setLevel(logging.DEBUG)
        pytuya_log.addHandler(h)
        pytuya_log.propagate = True

        def _log(msg: str) -> None:
            h.records.append(msg)
            _log_main = logging.getLogger("tuya_gui.status")
            _log_main.debug("%s %s", dev_id[:8], msg)
            print(f"[DEBUG] {msg}")   # stampa anche sul terminale

        # Helper per filtrare solo chiavi numeriche
        def _filter_numeric(dps_dict: dict) -> dict:
            if not isinstance(dps_dict, dict):
                return {}
            filtered = {}
            for k, v in dps_dict.items():
                if isinstance(k, int):
                    filtered[k] = v
                elif isinstance(k, str) and k.isdigit():
                    filtered[int(k)] = v
            return filtered

        # Estrae DPS da una risposta di pytuya
        def _extract_dps(res) -> dict:
            _log(f"status() raw result: type={type(res).__name__} repr={repr(res)[:300]}")
            if not res:
                return {}
            if isinstance(res, dict):
                if "dps" in res and isinstance(res["dps"], dict):
                    filtered = _filter_numeric(res["dps"])
                    if filtered:
                        _log(f"DPS from res['dps']: {list(filtered.keys())}")
                        return filtered
                if "parent" in res and isinstance(res["parent"], dict):
                    filtered = _filter_numeric(res["parent"])
                    if filtered:
                        _log(f"DPS from res['parent']: {list(filtered.keys())}")
                        return filtered
                filtered = _filter_numeric(res)
                if filtered:
                    _log(f"DPS from direct dict: {list(filtered.keys())}")
                    return filtered
            return {}

        # Legge la cache interna di pytuya
        def _proto_dps_cache(proto) -> dict:
            for attr in ("dps", "_dps", "dps_cache", "_dps_cache", "status_cache"):
                val = getattr(proto, attr, None)
                if isinstance(val, dict) and val:
                    if isinstance(val.get("parent"), dict):
                        filtered = _filter_numeric(val["parent"])
                        if filtered:
                            _log(f"proto.{attr}['parent'] cache hit: {list(filtered.keys())}")
                            return filtered
                    filtered = _filter_numeric(val)
                    if filtered:
                        _log(f"proto.{attr} cache hit: {list(filtered.keys())}")
                        return filtered
                    for cache_key, cache_val in val.items():
                        if isinstance(cache_val, dict):
                            filtered = _filter_numeric(cache_val)
                            if filtered:
                                _log(f"proto.{attr}[{cache_key!r}] cache hit: {list(filtered.keys())}")
                                return filtered
            return {}

        # Tentativo di detect_available_dps
        async def _try_detect(proto) -> dict:
            try:
                _log("detect_available_dps() → sending…")
                detected = await asyncio.wait_for(proto.detect_available_dps(), timeout=t+2)
                _log(f"detect_available_dps() returned: {repr(detected)[:200]}")
                dps = _extract_dps(detected)
                if not dps:
                    dps = _proto_dps_cache(proto)
                return dps
            except (Exception, asyncio.CancelledError) as exc:
                _log(f"detect_available_dps() exception: {exc}")
                return {}

        # Tentativo di status()
        async def _try_status(proto, label="") -> dict:
            try:
                _log(f"status(){' '+label if label else ''} → sending…")
                res = await asyncio.wait_for(proto.status(), timeout=t+2)
                dps = _extract_dps(res)
                if not dps:
                    dps = _proto_dps_cache(proto)
                return dps
            except (Exception, asyncio.CancelledError) as exc:
                _log(f"status(){' '+label if label else ''} exception: {exc}")
                return {}

        # Attesa push progressiva (4,10,30,60 secondi)
        async def _wait_for_push(proto, wait_times=None, listener=None):
            if wait_times is None:
                wait_times = [4, 10, 30, 60]
            pushed = {}
            event = asyncio.Event()

            def _on_push(data: dict) -> None:
                _log(f"push callback: {repr(data)[:200]}")
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(k, int) or (isinstance(k, str) and k.isdigit()):
                            pushed[int(k)] = v
                    if pushed:
                        event.set()

            if listener is not None:
                _log("Using connect-time TuyaListener for push updates")
                cached = _extract_dps(getattr(listener, "latest", {}))
                if cached:
                    return cached
            else:
                # Registra callback, se supportato dalla versione pytuya caricata.
                for setter in ("set_updater", "add_listener", "set_status_callback"):
                    fn = getattr(proto, setter, None)
                    if callable(fn):
                        try:
                            fn(_on_push)
                            _log(f"Registered push via {setter}")
                            break
                        except Exception as exc:
                            _log(f"{setter} failed: {exc}")

            # Ciclo di attesa progressivo
            for step, wait_sec in enumerate(wait_times, 1):
                # Invia heartbeat prima di ogni attesa
                heartbeat_ok = True
                try:
                    _log(f"Sending heartbeat (step {step})")
                    await asyncio.wait_for(proto.heartbeat(), timeout=5)
                    _log("Heartbeat sent OK")
                except (Exception, asyncio.CancelledError) as exc:
                    heartbeat_ok = False
                    _log(f"Heartbeat error: {exc}")
                if not heartbeat_ok or not getattr(proto, "is_connected", False):
                    _log("Socket is closed; stopping push wait")
                    break

                _log(f"Waiting {wait_sec}s for device push (step {step}/{len(wait_times)})...")
                try:
                    if listener is not None:
                        pushed_status = await asyncio.wait_for(listener.queue.get(), timeout=wait_sec)
                        dps = _extract_dps(pushed_status)
                        if not dps:
                            dps = _proto_dps_cache(proto)
                        if dps:
                            _log(f"Push received at step {step}: {list(dps.keys())}")
                            return dps
                    else:
                        await asyncio.wait_for(event.wait(), timeout=wait_sec)
                        if pushed:
                            _log(f"Push received at step {step}: {list(pushed.keys())}")
                            return _filter_numeric(pushed)
                except asyncio.TimeoutError:
                    _log(f"No push after {wait_sec}s, checking cache")
                except asyncio.CancelledError as exc:
                    _log(f"Push wait cancelled: {exc}")
                    break

                cached = _proto_dps_cache(proto)
                if cached:
                    _log(f"Cache hit after step {step}: {list(cached.keys())}")
                    return cached

            _log("All push wait steps exhausted, no data")
            return {}

        async def _try_listener_status(conn_cfg: dict) -> dict:
            """Fresh v3.4/v3.5 read path that mirrors Advanced Scan."""
            listener = QueueTuyaListener(_log)
            proto = None
            try:
                _log("Opening dedicated listener connection for v3.4+ status")
                proto = await asyncio.wait_for(
                    connect(
                        address=conn_cfg["host"],
                        device_id=conn_cfg["device_id"],
                        local_key=conn_cfg["local_key"],
                        protocol_version=float(conn_cfg.get("protocol_version", 3.4)),
                        enable_debug=True,
                        listener=listener,
                        port=int(conn_cfg.get("port", 6668)),
                        timeout=15,
                    ),
                    timeout=20,
                )
                _log("Dedicated listener connection obtained")

                dps = await _try_detect(proto)
                if dps:
                    _log(f"Dedicated listener got DPS via detect: {list(dps.keys())}")
                    return dps

                dps = await _try_status(proto, "(listener)")
                if dps:
                    _log(f"Dedicated listener got DPS via status: {list(dps.keys())}")
                    return dps

                wait_seq = [4, 10, min(max(t, 10), 30)]
                dps = await _wait_for_push(proto, wait_times=wait_seq, listener=listener)
                if dps:
                    _log(f"Dedicated listener got DPS via push: {list(dps.keys())}")
                    return dps
                return {}
            except (Exception, asyncio.CancelledError) as exc:
                _log(f"Dedicated listener status exception: {type(exc).__name__}: {exc}")
                return {}
            finally:
                if proto and getattr(proto, "transport", None):
                    try:
                        proto.transport.close()
                    except Exception:
                        pass

        # Costruzione risposta finale
        async def _build_result(dps: dict, source: str) -> dict:
            funcs = await _get_cloud_functions_cached(dev_id, conn_cfg)
            display_dps, display_units = _display_status_from_model(dps, conn_cfg, funcs)
            return {
                "status": dps,
                "display_status": display_dps,
                "display_units": display_units,
                "source": source,
                "tech_logs": "\\n".join(h.records),
            }

        try:
            conn_cfg = await _connection_config(dev_id, d)
            if conn_cfg.get("_cloud_key_refreshed"):
                _log("Using refreshed local_key from Tuya Cloud")

            proto_ver = float(conn_cfg.get("protocol_version", 3.3))
            is_push_device = proto_ver >= 3.4
            _log(f"protocol_version={proto_ver}, push_mode={is_push_device}")

            if is_push_device:
                _conn_pool.invalidate(dev_id)
                _log("v3.4+ device: trying dedicated listener strategy first")
                dps = await _try_listener_status(conn_cfg)
                if dps:
                    return await _build_result(dps, "local-listener")
                _log("Dedicated listener strategy returned no DPS; skipping pooled LAN for v3.4+")
            else:
                # Un solo tentativo LAN (con attesa push lunga), poi fallback immediato a HA
                _log("Starting LAN attempt with progressive push wait...")
                try:
                    proto = await _conn_pool.get(dev_id, conn_cfg)
                    _log("Pool connection obtained")

                    # 1. detect_available_dps
                    dps = await _try_detect(proto)
                    if dps:
                        _log(f"Got DPS via detect: {list(dps.keys())}")
                        return await _build_result(dps, "local")

                    # 2. status()
                    dps = await _try_status(proto, "(first)")
                    if dps:
                        _log(f"Got DPS via status: {list(dps.keys())}")
                        return await _build_result(dps, "local")

                    # 3. push-wait (solo v3.4+)
                    if is_push_device:
                        _log("v3.4+ device: starting progressive push-wait")
                        wait_seq = [4, 10, min(max(t, 10), 30)]
                        dps = await _wait_for_push(proto, wait_times=wait_seq)
                        if dps:
                            _log(f"Got DPS via push-wait: {list(dps.keys())}")
                            return await _build_result(dps, "local-push")

                    # Se arriviamo qui, LAN ha fallito
                    _conn_pool.invalidate(dev_id)
                    _log("LAN attempt failed, falling back to Home Assistant/Cloud")

                except (Exception, asyncio.CancelledError) as exc:
                    _log(f"LAN exception: {exc}")
                    _conn_pool.invalidate(dev_id)

            # FALLBACK: Home Assistant + Cloud
            ha_dps = _ha_states_as_dps(dev_id, conn_cfg)
            cloud_dps = await _cloud_status_as_dps(dev_id, conn_cfg)
            _log(f"HA DPS keys: {list(ha_dps.keys())}")
            _log(f"Cloud DPS keys: {list(cloud_dps.keys())}")

            valid_ha_dps = {
                dp: value
                for dp, value in ha_dps.items()
                if str(value).strip().lower() not in {"unknown", "unavailable", "none", ""}
            }
            fallback_dps = dict(cloud_dps)
            fallback_dps.update(valid_ha_dps)
            if fallback_dps:
                funcs = await _get_cloud_functions_cached(dev_id, conn_cfg)
                local_scaled = _local_scaling_by_dp(conn_cfg)
                already_scaled = {str(dp) for dp in valid_ha_dps if str(dp) in local_scaled}
                display_dps, display_units = _display_status_from_model(fallback_dps, conn_cfg, funcs, already_scaled)
                source_parts = []
                if valid_ha_dps:
                    source_parts.append("homeassistant")
                if cloud_dps:
                    source_parts.append("cloud")
                source = "+".join(source_parts) if source_parts else "fallback"
                return {
                    "status": fallback_dps,
                    "display_status": display_dps,
                    "display_units": display_units,
                    "source": source,
                    "tech_logs": "\\n".join(h.records),
                }
            else:
                return {
                    "error": "No data from device and no HA/cloud fallback",
                    "error_type": "no_data",
                    "tech_logs": "\\n".join(h.records),
                }

        finally:
            pytuya_log.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        # Timeout maggiorato per permettere l'attesa push lunga (max ~104 secondi)
        res = future.result(timeout=120)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/device/<dev_id>/force_ha")
def api_force_ha(dev_id: str):
    devices = get_devices_data()
    d = devices.get(dev_id)
    if not d:
        return jsonify({"error": "Unknown device"}), 404
    ha_dps = _ha_states_as_dps(dev_id, d)
    if not ha_dps:
        return jsonify({"error": "No HA state found"}), 404
    # Usa le stesse funzioni di scaling
    loop_for_ha = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_for_ha)
    funcs = loop_for_ha.run_until_complete(_get_cloud_functions_cached(dev_id, d))
    display, units = _display_status_from_model(ha_dps, d, funcs)
    return jsonify({
        "status": ha_dps,
        "display_status": display,
        "display_units": units,
        "source": "forced_ha",
        "tech_logs": "Forced Home Assistant fallback"
    })

@app.route("/api/device/<dev_id>/cloud_check")
def api_cloud_check(dev_id: str):
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503
    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry["domain"] == "localtuya":
            cloud_conf = entry["data"]
            break
    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            
            h.records.append(f"=== CLOUD CHECK ===")
            h.records.append(f"Device ID: {dev_id}")
            
            funcs = await api.async_get_device_functions(dev_id)
            for dp in funcs:
                if "values" in funcs[dp]:
                    try:
                        funcs[dp]["values"] = json.loads(funcs[dp]["values"])
                    except Exception:
                        pass
            dps = {
                str(dp): info.get("value")
                for dp, info in funcs.items()
                if isinstance(info, dict) and "value" in info
            }
            cfg = get_devices_data().get(dev_id, {"device_id": dev_id})
            display, units = _display_status_from_model(dps, cfg, funcs)
            return {
                "result": funcs,
                "status": dps,
                "display_status": display,
                "display_units": units,
                "source": "cloud-shadow",
                "tech_logs": "\\n".join(h.records),
            }
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=20))
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------------------------------------------------------------------
# /api/device/<dev_id>/custom_cloud_request  — custom Tuya Cloud API requests
# ---------------------------------------------------------------------------
@app.route("/api/device/<dev_id>/custom_cloud_request", methods=["POST"])
def api_custom_cloud_request(dev_id: str):
    """Send a custom request to Tuya Cloud API.
    
    Expected JSON body:
    {
        "method": "GET|POST|PUT|DELETE",
        "path": "/v1.0/expand/devices/{device_id}",
        "body": {}  # optional for POST/PUT
    }
    """
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503
    
    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break
    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404
    
    req = request.json or {}
    method = req.get("method", "GET").upper()
    path = req.get("path", "")
    body = req.get("body")
    
    if not path:
        return jsonify({"error": "path is required"}), 400
    
    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            
            # Log the request details
            h.records.append(f"=== CUSTOM CLOUD REQUEST ===")
            h.records.append(f"Device ID: {dev_id}")
            h.records.append(f"Method: {method}")
            h.records.append(f"Path: {path}")
            h.records.append(f"Body: {body}")
            
            # Use the internal async_make_request method
            result = await api.async_make_request(method, path, body)
            
            # Log the response
            h.records.append(f"=== RESPONSE ===")
            h.records.append(f"Response: {result}")
            
            return {
                "result": result,
                "tech_logs": "\\n".join(h.records),
            }
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=30))
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------------------------------------------------------------------
# /api/device/<dev_id>/cloud_device_details  — Detailed info for a specific device
# ---------------------------------------------------------------------------
@app.route("/api/device/<dev_id>/cloud_device_details", endpoint="api_cloud_device_details")
def api_cloud_device_details(dev_id: str):
    """Return detailed info for a specific device from Tuya Cloud."""
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            
            # Get device info - try multiple endpoints
            device_info = {}
            
            # Try 1: /v1.0/devices/{id}
            try:
                device_resp = await api.async_make_request("GET", f"/v1.0/devices/{dev_id}")
                h.records.append(f"Device info response (v1.0): {device_resp}")
                if device_resp.get("success") and device_resp.get("result"):
                    device_info = device_resp["result"]
                    h.records.append(f"SUCCESS: Got device info from /v1.0/devices/{dev_id}")
                else:
                    h.records.append(f"/v1.0/devices failed: {device_resp.get('msg', 'unknown')}")
                    
                    # Try /v1.1/devices/{id}/specifications
                    try:
                        spec_resp = await api.async_make_request("GET", f"/v1.1/devices/{dev_id}/specifications")
                        h.records.append(f"Specifications response: {spec_resp}")
                        if spec_resp.get("success") and spec_resp.get("result"):
                            device_info = spec_resp["result"]
                            h.records.append(f"SUCCESS: Got device info from specifications endpoint")
                    except Exception as e:
                        h.records.append(f"Warning: specifications failed: {e}")
                    
                    # If still no device info, try to get from cloud device list
                    if not device_info:
                        try:
                            devs = await api.async_get_devices_list(force_update=True)
                            if isinstance(devs, dict):
                                if dev_id in devs:
                                    device_info = devs[dev_id]
                                else:
                                    # Search by other ID fields
                                    for dev_key, dev_val in devs.items():
                                        if isinstance(dev_val, dict):
                                            if (dev_val.get("id") == dev_id or 
                                                dev_val.get("device_id") == dev_id or 
                                                dev_val.get("res_id") == dev_id or
                                                dev_val.get("deviceId") == dev_id or
                                                dev_key == dev_id):
                                                device_info = dev_val
                                                break
                        except Exception as e:
                            h.records.append(f"Warning: device list fallback failed: {e}")
            except Exception as e:
                h.records.append(f"Warning: /v1.0/devices failed: {e}")
            
            # Fallback: create minimal device info
            if not device_info:
                device_info = {"id": dev_id, "device_id": dev_id, "res_id": dev_id}
                h.records.append("WARNING: No device info retrieved - created minimal info")
            
            # Get device functions - handle permission errors gracefully
            funcs = {}
            try:
                funcs = await api.async_get_device_functions(dev_id)
                if funcs:
                    for dp in funcs:
                        if "values" in funcs[dp]:
                            try:
                                funcs[dp]["values"] = json.loads(funcs[dp]["values"])
                            except Exception:
                                pass
            except Exception as func_error:
                h.records.append(f"Warning: Could not fetch device functions: {func_error}")
                funcs = {}
            
            # Get factory info for MAC/SN/UUID
            factory_info = {}
            try:
                factory_info = await api.async_get_device_factory_info(dev_id)
            except Exception as factory_error:
                h.records.append(f"Warning: Could not fetch factory info: {factory_error}")
            
            return {
                "device_info": device_info,
                "functions": funcs,
                "factory_info": factory_info,
                "tech_logs": "\\n".join(h.records),
            }
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=30))
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------------------------------------------------------------------
# /api/device/<dev_id>/command  — uses connection pool
# ---------------------------------------------------------------------------
@app.route("/api/device/<dev_id>/command", methods=["POST"])
def api_command(dev_id: str):
    if connect is None:
        return jsonify({"error": "LocalTuya core dependencies unavailable"}), 503
    devices = get_devices_data()
    d = devices.get(dev_id)
    if not d:
        return jsonify({"error": "Unknown device"}), 404
    req = request.json or {}

    async def _run():
        try:
            conn_cfg = await _connection_config(dev_id, d)
            proto = await _conn_pool.get(dev_id, conn_cfg)
            await proto.detect_available_dps()
            await proto.set_dps(req.get("dps", {}))
            await asyncio.sleep(0.5)
            return {"result": "ok"}
        except ConnectionResetError as exc:
            _conn_pool.invalidate(dev_id)
            return {"error": f"Device reset the connection: {exc}", "error_type": "connection_reset"}
        except (asyncio.TimeoutError, TimeoutError) as exc:
            _conn_pool.invalidate(dev_id)
            return {"error": f"Timeout sending command: {exc}", "error_type": "timeout"}
        except Exception as exc:
            _conn_pool.invalidate(dev_id)
            return {"error": str(exc), "error_type": "unknown"}

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        t = int(req.get("timeout", 10))
        return jsonify(future.result(timeout=max(t + 10, 35)))
    except Exception as e:
        return jsonify({"error": str(e)})
# ---------------------------------------------------------------------------
# /api/cloud/spaces  — Get all spaces from Tuya Cloud
# ---------------------------------------------------------------------------
@app.route("/api/cloud/spaces")
def api_cloud_spaces():
    """Return all spaces from Tuya Cloud."""
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            
            # Get spaces from cloud
            spaces = await api.async_get_spaces()
            
            return {
                "spaces": spaces,
                "tech_logs": "\\n".join(h.records),
            }
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=30))
    except Exception as e:
        return jsonify({"error": str(e)})
# ---------------------------------------------------------------------------
# /api/cloud/spaces/<space_id>/resources  — Get resources for a specific space
# ---------------------------------------------------------------------------
@app.route("/api/cloud/spaces/<space_id>/resources")
def api_cloud_space_resources(space_id):
    """Return all resources for a specific space from Tuya Cloud."""
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            
            # Get resources for the specific space
            resources = await api.async_get_space_resources(space_id)
            
            return {
                "resources": resources,
                "tech_logs": "\\n".join(h.records),
            }
        except Exception as e:
            return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=30))
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------------------------------------------------------------------
# /api/cloud/spaces/<space_id>/resources_raw  — Raw Tuya Cloud API response (LocalTuya-compatible format)
# ---------------------------------------------------------------------------
@app.route("/api/cloud/spaces/<space_id>/resources_raw")
def api_cloud_space_resources_raw(space_id):
    """Return raw Tuya Cloud API response for space resources (LocalTuya 'Lista Dispositivi' compatible format)."""
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            raw_resp = await api.async_make_request("GET", f"/v2.0/cloud/space/{space_id}/resource")
            return raw_resp
        except Exception as e:
            return {"error": str(e)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=30))
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------------------------------------------------------------------------
# /api/cloud/devices-list  — Return TuyaCloudApi's cached device_list (all cloud device details)
# ---------------------------------------------------------------------------
@app.route("/api/cloud/devices-list")
def api_cloud_devices_list():
    """Return the full cached TuyaCloudApi device_list (all cloud devices with details)."""
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger("cloud_api")
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf["region"],
                cloud_conf["client_id"],
                cloud_conf["client_secret"],
                cloud_conf["user_id"],
            )
            await api.async_connect()
            # Ensure device_list is populated
            await api.async_get_devices_list()
            return {"result": list(api.device_list.values())}
        except Exception as e:
            return {"error": str(e)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=30))
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
