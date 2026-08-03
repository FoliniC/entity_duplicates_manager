"""
HALog2026 — Unified Pyscript Service Layer
==========================================
Exposes a single pyscript.halog2026_write service consumed by all
YAML log listeners.

Subsystem-specific enrichment (e.g. power reading for scale) is handled
via the _ENRICHERS dict — add a callable there to extend without touching
the core write path.

Deploy to: /config/pyscript/modules/halog2026_events_write.py
Lib at:    /config/pyscript/lib/halog2026_lib.py
"""

import sys
import os

# Absolute path for HA docker
LIB_PATH = "/config/pyscript/lib"
if LIB_PATH not in sys.path:
    sys.path.append(LIB_PATH)

try:
    import halog2026_lib
except ImportError as e:
    # Fallback to local relative
    sys.path.append("./pyscript/lib")
    import halog2026_lib

# ── Helper to get pyscript decorators at call time (lazy) ─────────────────────
# This avoids the module being imported with dummy decorators when HA's config
# validation imports the file. The decorators are only resolved when pyscript
# actually executes the file in its own context.

class _Service:
    """Service object that mimics pyscript's service object with both decorator and call() method."""
    def __call__(self, *args, **kwargs):
        """Decorator interface: @service"""
        if len(args) == 1 and callable(args[0]):
            return args[0]
        def decorator(func):
            return func
        return decorator
    
    def call(self, domain, service, **kwargs):
        """Call a service: service.call(domain, service, **kwargs)"""
        if not _IN_PYSCRIPT:
            return
        # In pyscript, this would be: service.call(domain, service, **kwargs)
        # We use the task.executor to call the service
        return task.executor(service.call, *args, **kwargs)

# Get decorators at module load time (will be dummy if not in pyscript context)
try:
    event_trigger
    service_obj = _Service()
    service = service_obj
    time_trigger
    _IN_PYSCRIPT = True
except NameError:
    _IN_PYSCRIPT = False
    
    class _DummyService:
        def __call__(self, *args, **kwargs):
            if len(args) == 1 and callable(args[0]):
                return args[0]
            def decorator(func):
                return func
            return decorator
        
        def call(self, *args, **kwargs):
            pass
    
    _dummy_service = _DummyService()
    event_trigger = lambda *args, **kwargs: (lambda func: func)
    service = _DummyService()
    time_trigger = lambda *args, **kwargs: (lambda func: func)
    _IN_PYSCRIPT = False

# ── Subsystem enrichers ───────────────────────────────────────────────────────
# Each enricher receives the kwargs dict and returns an extra string that is
# inserted between [LEVEL] and the message body.
# HA state is accessible here because these run inside pyscript.

def _enrich_scale(kwargs: dict) -> str:
    action_map = {
        "acceso":    "accensione",
        "spento":    "spegnimento",
        "nulla":     "invariato",
        "debug":     "debug",
        "toggle":    "toggle",
        "attuatore": "attuatore",
    }
    # Se manca l'azione, usiamo 'debug' come default per questo sottosistema
    action_raw = kwargs.get("action", "debug")
    mapped = action_map.get(action_raw, action_raw)
    try:
        p1    = float(state.get("sensor.sonoff_10024024c4_power_1") or 0)
        p2    = float(state.get("sensor.sonoff_10024024c4_power_2") or 0)
        power = p1 + p2
    except Exception:
        power = 0.0
    light = "ACCESA 💡" if power > 12 else "SPENTA 🌑"
    return f" [{mapped}] [Luce: {light} Power: {power:.2f}W]"


# Map subsystem name → enricher function.  Add entries here to extend.
_ENRICHERS: dict = {
    "scale": _enrich_scale,
}

# ── Global state ──────────────────────────────────────────────────────────────
_IS_STARTED = False

# ── Private helper (sync, for internal calls within this file) ────────────────

def _write_direct(subsystem: str, message: str, level: str = "INFO") -> None:
    """Synchronous write with no enrichment — used for internal log messages."""
    if not _IN_PYSCRIPT:
        return
    from datetime import datetime
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} [{level.upper()}] {message.strip()}\n"
    task.executor(halog2026_lib.sync_write_log, subsystem, line)


# ── Core public service ───────────────────────────────────────────────────────

@event_trigger("halog2026_write_event")
async def halog2026_handle_event(subsystem=None, message="", level="INFO", **kwargs):
    """
    Escuta l'evento 'halog2026_write_event' e lo inoltra al sistema di scrittura.
    Questo evita errori di 'Service not found' nello YAML al boot.
    """
    if not _IN_PYSCRIPT:
        return
    if not subsystem:
        return
    await halog2026_write(subsystem=subsystem, message=message, level=level, **kwargs)

@service
async def halog2026_write(
    subsystem: str = "",
    message:   str = "",
    level:     str = "INFO",
    **kwargs,
):
    """
    Universal log writer — route all subsystem log events here.

    Parameters
    ----------
    subsystem : str
        One of the keys in halog2026_lib.SUBSYSTEMS  (fancoil | ev | scale)
        or any new subsystem registered there.
    message : str
        Log message body.
    level : str
        Severity label: INFO, WARNING, ERROR, SYSTEM, DEBUG, …
    **kwargs
        Subsystem-specific extras:
          scale → action (str), wait (int, seconds to delay before writing)
    """
    if not _IN_PYSCRIPT:
        return
    from datetime import datetime

    wait_secs = int(kwargs.get("wait", 0))
    if wait_secs > 0:
        await task.sleep(wait_secs)

    ts        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    enricher  = _ENRICHERS.get(subsystem)
    extra     = enricher(kwargs) if enricher else ""
    line      = f"{ts} [{level.upper()}]{extra} {message.strip()}\n"

    await task.executor(halog2026_lib.sync_write_log, subsystem, line)


# ── Boot-buffer flush ─────────────────────────────────────────────────────────

@service
def halog2026_flush_boot_buffer(
    entity_id: str = None,
    subsystem: str = "fancoil",
):
    """
    Writes the pre-formatted boot buffer stored in an HA entity attribute
    directly to the subsystem log, then logs a summary line.

    The buffer uses [[BR]] as a newline placeholder (HA attribute limit).
    """
    if not _IN_PYSCRIPT:
        return
    if not entity_id:
        return
    try:
        raw = state.getattr(entity_id).get("log_queue", "")
        if not raw:
            return
        content = raw.replace("[[BR]]", "\n")
        print(f"[HALog2026] flush_boot_buffer [{subsystem}]: {len(content)} chars")
        task.executor(halog2026_lib.sync_write_log, subsystem, "\n" + content)
        n = content.count("\n")
        _write_direct(subsystem, f"Boot buffer flushed ({n} messages)", "SYSTEM")
    except Exception as e:
        _write_direct(subsystem, f"Boot buffer flush error: {e}", "ERROR")


# ── State persistence ─────────────────────────────────────────────────────────

@service
def halog2026_state_save(
    subsystem: str = "fancoil",
    entity_id: str = None,
    value             = None,
):
    """Persists a single HA entity value to the subsystem state JSON file."""
    if not _IN_PYSCRIPT:
        return
    if not entity_id:
        return
    task.executor(halog2026_lib.sync_save_state, subsystem, entity_id, value)


@service
def halog2026_states_restore(subsystem: str = "fancoil"):
    """
    Reads the persisted state JSON for *subsystem* and restores
    input_number / input_boolean entities to their saved values.
    Respects a 5-minute grace period for manual changes.
    """
    if not _IN_PYSCRIPT:
        return
    from datetime import datetime, timedelta
    
    states = task.executor(halog2026_lib.sync_read_states, subsystem)
    if not states:
        return
    
    now = datetime.now()
    
    for eid, val in states.items():
        domain = eid.split(".")[0]
        
        # Check if the state was recently changed manually (last 5 minutes)
        last_changed = state.get(eid, attribute='last_changed')
        if last_changed:
            # last_changed is a datetime object in pyscript
            if now - last_changed < timedelta(seconds=300):
                _write_direct(subsystem, f"Skipping restore for {eid} (manual change < 5min)", "INFO")
                continue
        
        try:
            if domain == "input_number":
                input_number.set_value(entity_id=eid, value=float(val))
            elif domain == "input_boolean":
                if val in ["on", "True", True]:
                    input_boolean.turn_on(entity_id=eid)
                else:
                    input_boolean.turn_off(entity_id=eid)
        except Exception:
            pass
    _write_direct(subsystem, "State restore from file completed", "SYSTEM")


# ── Startup (Double-Safety listener activation + session header) ──────────────

@time_trigger("startup")
async def halog2026_startup():
    if not _IN_PYSCRIPT:
        return
    global _IS_STARTED
    if _IS_STARTED:
        log.info("HALog2026: Startup already performed, skipping.")
        return
    _IS_STARTED = True
    
    from datetime import datetime

    # 1 — Archive logs that have grown beyond their configured max size
    for sub in halog2026_lib.SUBSYSTEMS:
        task.executor(halog2026_lib.sync_archive_log, sub)

    # 2 — Session header
    from datetime import datetime
    now_str = datetime.now().strftime("%H:%M:%S")
    uptime_str = "not_available"
    
    # [LOGIC COMMENTED TO AVOID BOOT CRASH]
    # Uptime calculation removed for stability at startup.

    msg = (
        f"=== HALog2026 / Pyscript started (New Log Session) | "
        f"Config: {halog2026_lib.JSON_CONFIG_PATH} ==="
    )
    
    # Scrivi l'header per tutti i sottosistemi configurati
    for sub in halog2026_lib.SUBSYSTEMS:
        _write_direct(sub, msg, "SYSTEM")
    system_log.write(level="info", logger="halog2026", message=msg)

    # 3 — Flush boot buffer (fancoil subsystem)
    halog2026_flush_boot_buffer(
        entity_id="input_boolean.fancoil_boot_buffering",
        subsystem="fancoil",
    )
    service.call("input_text", "set_value", entity_id="input_text.fancoil_boot_semaphore", value="none")

    # NOTE: Listener activation is NOT needed here.
    # All listeners have initial_state: true and are activated automatically.
    # The boot manager (halog2026_boot_manager.yaml) confirms this.
    # The previous Double-Safety code ran too early (at startup trigger)
    # and caused "Referenced entities ... are missing" warnings.