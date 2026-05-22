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

# v1.2.1 - Refresh stale local_key from Tuya Cloud at runtime and classify
#          session-key negotiation failures explicitly.
VERSION = "1.2.4"

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
    import traceback
    print("Dependencies not found. Traceback follows:")
    traceback.print_exc()
    print("Set LOCALTUYA_CORE_PATH to localtuya/core path.")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
_log = logging.getLogger("tuya_gui")
_log.info("=== tuya_gui %s starting ===", VERSION)
_log.info("connect=%s  TuyaCloudApi=%s", connect, TuyaCloudApi)

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
    1) /proc/net/arp  (fast, no extra deps)
    2) ``ip neigh show <ip>``  (requires iproute2)
    """
    if not ip or not isinstance(ip, str):
        return None
    ip = ip.strip()
    if not ip:
        return None

    # 1) ARP cache
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

    # 2) ip neigh
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
    cloud = cloud_devices.get(cloud_id) or cloud_devices.get(dev_id) or {}
    status_items = cloud.get("status") if isinstance(cloud, dict) else None
    if not isinstance(status_items, list):
        return {}

    funcs = await _get_cloud_functions_cached(dev_id, cfg)
    if not isinstance(funcs, dict):
        return {}

    code_to_dp = {
        info.get("code"): str(dp_id)
        for dp_id, info in funcs.items()
        if isinstance(info, dict) and info.get("code")
    }

    dps = {}
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
        .main { flex: 2.5; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
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
    </div>

    <div id="tabManage" class="container tab-content active">
        <div class="sidebar">
            <label>Sort</label>
            <select id="sort" onchange="updateSort(this.value)">
                <option value="name">Name</option><option value="ip">IP</option><option value="usage">Usage</option>
            </select>
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
                <div><label>Timeout</label><input type="number" id="timeout" value="10"></div>
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
            </div>
            <div id="manualDiscoveryLogs" style="font-size:11px; color:#666; padding:8px; background:#f5f5f5; border-radius:4px; max-height:100px; overflow-y:auto; margin-bottom:12px; display:none;">
                Scanning...
            </div>

            <label style="margin-top:16px;">Cloud devices not yet configured</label>
            <div style="display:flex; gap:8px; margin-bottom:8px;">
                <button class="btn-cloud" style="flex:1" onclick="loadUnaddedDevices()">Refresh Unadded</button>
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
            document.getElementById('tabManage').classList.toggle('active', isManage);
            document.getElementById('tabAdd').classList.toggle('active', !isManage);
            document.getElementById('tabManageBtn').classList.toggle('active', isManage);
            document.getElementById('tabAddBtn').classList.toggle('active', !isManage);
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
                    logsBox.innerText += "\\n\\n--- CLOUD JSON RESULT ---\\n" + JSON.stringify(data.result, null, 2);
                    renderTable(); 
                } else { alert(data.error); }
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }
        function renderTable() {
            const mapping = devices[selectedId].entities || [];
            const allIds = new Set([...Object.keys(currentDps), ...Object.keys(cloudDps)]);
            document.getElementById('dpBody').innerHTML = Array.from(allIds).sort((a,b)=>Number(a)-Number(b)).map(id => {
                const displayVal = currentDisplayDps[id] !== undefined ? currentDisplayDps[id] : currentDps[id];
                const unit = currentDisplayUnits[id] ? ` ${currentDisplayUnits[id]}` : '';
                const localVal = currentDps[id] !== undefined ? `${displayVal}${unit}` : '<span style="color:#999">?</span>';
                const cloudInfo = cloudDps[id] || {};
                const entity = mapping.find(e => e.id == id);
                return `<tr onclick="onRowClick(${JSON.stringify(id)}, ${JSON.stringify(String(currentDps[id] ?? ''))})" style="cursor:pointer">
                    <td><b>${id}</b></td><td>${entity?entity.friendly_name:(cloudInfo.name || 'Unknown')}</td>
                    <td>${localVal}</td><td><small>${cloudInfo.code || '-'}</small></td>
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
                    info += `\nStatus: ${dev.status || 'unknown'}\\n`;
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


# ---------------------------------------------------------------------------
# /api/device/discover_by_ip  — discover Tuya device at IP via local scan
# ---------------------------------------------------------------------------
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

        def _proto_dps_cache(proto) -> dict:
            """Extract any DPS cached by pytuya on the protocol object."""
            for attr in ("dps", "_dps", "dps_cache", "_dps_cache", "status_cache"):
                val = getattr(proto, attr, None)
                if isinstance(val, dict) and val:
                    _log(f"[tuya_gui] proto.{attr} cache hit: {list(val.keys())} = {val}")
                    return dict(val)
            _log("[tuya_gui] proto: no DPS cache attributes found")
            return {}

        def _extract_dps(res) -> dict:
            """Pull DPS out of whatever status() returned, logging every step."""
            _log(f"[tuya_gui] status() raw result: type={type(res).__name__} repr={repr(res)[:300]}")
            if not res:
                _log("[tuya_gui] status() returned falsy value — no DPS")
                return {}
            if isinstance(res, dict):
                # Case 1: {"dps": {...}}
                if "dps" in res and isinstance(res["dps"], dict):
                    _log(f"[tuya_gui] DPS extracted from res['dps']: {list(res['dps'].keys())}")
                    return dict(res["dps"])
                # Case 2: res IS the dps dict (all-int or all-str keys)
                if res and all(isinstance(k, (int, str)) for k in res):
                    _log(f"[tuya_gui] res looks like a raw DPS dict: {list(res.keys())}")
                    return dict(res)
            _log(f"[tuya_gui] Could not extract DPS from: {repr(res)[:200]}")
            return {}

        async def _try_detect(proto) -> dict:
            """Call detect_available_dps() and return whatever it gives us."""
            try:
                _log("[tuya_gui] detect_available_dps() → sending…")
                detected = await asyncio.wait_for(proto.detect_available_dps(), timeout=t + 2)
                _log(f"[tuya_gui] detect_available_dps() returned: {repr(detected)[:200]}")
                dps = _extract_dps(detected)
                if not dps:
                    dps = _proto_dps_cache(proto)
                return dps
            except Exception as exc:
                _log(f"[tuya_gui] detect_available_dps() exception: {exc}")
                return {}

        async def _try_status(proto, label: str = "") -> dict:
            """Call status(), extract DPS and check cache."""
            try:
                _log(f"[tuya_gui] status(){' ' + label if label else ''} → sending…")
                res = await asyncio.wait_for(proto.status(), timeout=t + 2)
                dps = _extract_dps(res)
                if not dps:
                    dps = _proto_dps_cache(proto)
                return dps
            except Exception as exc:
                _log(f"[tuya_gui] status(){' ' + label if label else ''} exception: {exc}")
                return {}

        async def _wait_for_push(proto, wait_s: float = 3.0) -> dict:
            """For v3.4/v3.5 devices that send DPS via push instead of
            responding to active queries: wait for a push event.
            Tries set_updater callback first; falls back to polling proto.dps."""
            pushed: dict = {}
            event = asyncio.Event()

            def _on_push(data: dict) -> None:
                _log(f"[tuya_gui] push callback received: {repr(data)[:200]}")
                if isinstance(data, dict):
                    pushed.update(data)
                    event.set()

            # 1) Try callback-based listener
            for setter in ("set_updater", "add_listener", "set_status_callback"):
                fn = getattr(proto, setter, None)
                if callable(fn):
                    try:
                        fn(_on_push)
                        _log(f"[tuya_gui] Registered push listener via proto.{setter}()")
                        break
                    except Exception as exc:
                        _log(f"[tuya_gui] proto.{setter}() failed: {exc}")

            # 2) Send heartbeat to tickle the device into sending a status push
            try:
                _log("[tuya_gui] Sending heartbeat to trigger push…")
                await asyncio.wait_for(proto.heartbeat(), timeout=5)
                _log("[tuya_gui] Heartbeat sent OK")
            except Exception as exc:
                _log(f"[tuya_gui] Heartbeat error (non-fatal): {exc}")

            # 3) Wait for the push event or fall back to polling proto.dps
            _log(f"[tuya_gui] Waiting {wait_s}s for device push…")
            try:
                await asyncio.wait_for(event.wait(), timeout=wait_s)
                _log(f"[tuya_gui] Push event received: {list(pushed.keys())}")
            except asyncio.TimeoutError:
                _log("[tuya_gui] No push event in time — checking proto.dps cache")

            # 4) Merge pushed data with proto.dps cache
            dps = dict(pushed) if pushed else {}
            cached = _proto_dps_cache(proto)
            if cached and not dps:
                dps = cached
            elif cached:
                cached.update(dps)
                dps = cached

            _log(f"[tuya_gui] _wait_for_push result: {dps}")
            return dps

        async def _build_result(dps: dict, source: str) -> dict:
            """Build the final API response dict from a DPS dict."""
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
                _log("[tuya_gui] Using refreshed local_key from Tuya Cloud")

            proto_ver = float(conn_cfg.get("protocol_version", 3.3))
            is_push_device = proto_ver >= 3.4
            _log(f"[tuya_gui] protocol_version={proto_ver}, push_mode={is_push_device}")

            for attempt in range(3):
                _log(f"[tuya_gui] === Attempt {attempt + 1}/3 ===")
                try:
                    # ----------------------------------------------------------
                    # Attempt 0 & 1: pool connection
                    # Attempt 2: fresh direct connection (bypasses pool)
                    # ----------------------------------------------------------
                    if attempt < 2:
                        proto = await _conn_pool.get(dev_id, conn_cfg)
                        _log(f"[tuya_gui] Pool connection obtained for {dev_id}")
                    else:
                        _conn_pool.invalidate(dev_id)
                        _log("[tuya_gui] Attempt 3: fresh direct connection (pool bypassed)")
                        proto = await asyncio.wait_for(
                            connect(
                                address=conn_cfg["host"],
                                device_id=conn_cfg["device_id"],
                                local_key=conn_cfg["local_key"],
                                protocol_version=proto_ver,
                                enable_debug=True,
                                timeout=t,
                            ),
                            timeout=t + 5,
                        )
                        _log("[tuya_gui] Fresh connection established")

                    # ----------------------------------------------------------
                    # Strategy A: detect_available_dps() — explicit call with log
                    # ----------------------------------------------------------
                    dps = await _try_detect(proto)
                    if dps:
                        _log(f"[tuya_gui] ✓ Got {len(dps)} DPS via detect_available_dps()")
                        return await _build_result(dps, "local")

                    # ----------------------------------------------------------
                    # Strategy B: status()
                    # ----------------------------------------------------------
                    dps = await _try_status(proto, label="(first call)")
                    if dps:
                        _log(f"[tuya_gui] ✓ Got {len(dps)} DPS via status()")
                        return await _build_result(dps, "local")

                    # ----------------------------------------------------------
                    # Strategy C: for v3.4/v3.5 — wait for device push
                    # ----------------------------------------------------------
                    if is_push_device:
                        _log("[tuya_gui] v3.4/v3.5 device: trying push-wait strategy")
                        dps = await _wait_for_push(proto, wait_s=4.0 if attempt < 2 else 6.0)
                        if dps:
                            _log(f"[tuya_gui] ✓ Got {len(dps)} DPS via push-wait")
                            return await _build_result(dps, "local-push")

                        # After push wait, try status() once more — device may
                        # have updated its internal cache during the wait
                        dps = await _try_status(proto, label="(after push-wait)")
                        if dps:
                            _log(f"[tuya_gui] ✓ Got {len(dps)} DPS via status() after wait")
                            return await _build_result(dps, "local")

                    # ----------------------------------------------------------
                    # All local strategies failed for this attempt
                    # ----------------------------------------------------------
                    _conn_pool.invalidate(dev_id)
                    logs = "\\n".join(h.records)

                    if _negotiation_failed(logs):
                        if attempt == 0:
                            conn_cfg = await _connection_config(
                                dev_id, d, force_cloud_update=True
                            )
                            if conn_cfg.get("_cloud_key_refreshed"):
                                _log("[tuya_gui] Refreshed local_key from cloud after negotiation failure")
                        if attempt < 2:
                            await asyncio.sleep(3)
                            continue
                        return {
                            "error": (
                                "Session key negotiation failed. "
                                "The local_key or protocol_version may be stale."
                            ),
                            "error_type": "negotiation_failed",
                            "tech_logs": logs,
                        }

                    if attempt < 2:
                        _log(f"[tuya_gui] No DPS from local on attempt {attempt + 1}, retrying…")
                        await asyncio.sleep(2)
                        continue

                    # ----------------------------------------------------------
                    # All 3 attempts exhausted — HA/cloud fallback
                    # ----------------------------------------------------------
                    _log("[tuya_gui] All local strategies failed — falling back to HA/cloud")
                    ha_dps = _ha_states_as_dps(dev_id, conn_cfg)
                    cloud_dps = await _cloud_status_as_dps(dev_id, conn_cfg)
                    _log(f"[tuya_gui] HA fallback DPs: {list(ha_dps.keys())}")
                    _log(f"[tuya_gui] Cloud fallback DPs: {list(cloud_dps.keys())}")
                    fallback_dps = dict(cloud_dps)
                    fallback_dps.update(ha_dps)
                    if fallback_dps:
                        funcs = await _get_cloud_functions_cached(dev_id, conn_cfg)
                        local_scaled = _local_scaling_by_dp(conn_cfg)
                        already_scaled_dps = {
                            str(dp_id)
                            for dp_id in ha_dps
                            if str(dp_id) in local_scaled
                        }
                        display_dps, display_units = _display_status_from_model(
                            fallback_dps, conn_cfg, funcs, already_scaled_dps
                        )
                        source_parts = []
                        if ha_dps:
                            source_parts.append("homeassistant")
                        if cloud_dps:
                            source_parts.append("cloud")
                        source = "+".join(source_parts)
                        _log(f"[tuya_gui] Fallback source: {source}")
                        return {
                            "status": fallback_dps,
                            "display_status": display_dps,
                            "display_units": display_units,
                            "source": source,
                            "tech_logs": "\\n".join(h.records),
                        }
                    return {
                        "error": "Device returned no data and no HA/cloud fallback available.",
                        "error_type": "no_data",
                        "tech_logs": "\\n".join(h.records),
                    }

                except ConnectionResetError as exc:
                    _conn_pool.invalidate(dev_id)
                    _log(f"[tuya_gui] ConnectionResetError on attempt {attempt + 1}: {exc}")
                    if attempt == 2:
                        return {
                            "error": f"Device closed the connection (ConnectionResetError): {exc}",
                            "error_type": "connection_reset",
                            "tech_logs": "\\n".join(h.records),
                        }
                    await asyncio.sleep(2)

                except (asyncio.TimeoutError, TimeoutError) as exc:
                    _conn_pool.invalidate(dev_id)
                    _log(f"[tuya_gui] TimeoutError on attempt {attempt + 1}: {exc}")
                    if attempt == 2:
                        return {
                            "error": f"Network timeout waiting for device: {exc}",
                            "error_type": "timeout",
                            "tech_logs": "\\n".join(h.records),
                        }
                    await asyncio.sleep(3)

                except Exception as exc:
                    _conn_pool.invalidate(dev_id)
                    _log(f"[tuya_gui] Exception on attempt {attempt + 1}: {type(exc).__name__}: {exc}")
                    logs = "\\n".join(h.records)
                    if _negotiation_failed(logs) and attempt == 0:
                        conn_cfg = await _connection_config(
                            dev_id, d, force_cloud_update=True
                        )
                        if conn_cfg.get("_cloud_key_refreshed"):
                            _log("[tuya_gui] Refreshed local_key from cloud after negotiation failure")
                    if attempt == 2:
                        if _negotiation_failed(logs):
                            return {
                                "error": (
                                    "Session key negotiation failed. "
                                    "The local_key or protocol_version may be stale."
                                ),
                                "error_type": "negotiation_failed",
                                "tech_logs": logs,
                            }
                        return {
                            "error": str(exc),
                            "error_type": "unknown",
                            "tech_logs": logs,
                        }
                    await asyncio.sleep(5)

            return {"error": "Max retries exceeded.", "error_type": "unknown", "tech_logs": "\\n".join(h.records)}
        finally:
            pytuya_log.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        res = future.result(timeout=max(t + 10, 35))
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)})


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
            funcs = await api.async_get_device_functions(dev_id)
            for dp in funcs:
                if "values" in funcs[dp]:
                    try:
                        funcs[dp]["values"] = json.loads(funcs[dp]["values"])
                    except Exception:
                        pass
            return {"result": funcs, "tech_logs": "\\n".join(h.records)}
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
