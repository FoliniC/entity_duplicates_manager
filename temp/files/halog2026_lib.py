"""
HALog2026 — Unified Home Assistant Logging Library
====================================================
Sync I/O layer: called exclusively via task.executor() from pyscript.
No Home Assistant APIs here — pure Python stdlib only.

To add a new subsystem, add one entry to SUBSYSTEMS. Nothing else needs
to change.
"""

import os
import json
from datetime import datetime
from typing import Any

# ── Subsystem registry ────────────────────────────────────────────────────────

BASE_LOG_DIR = "/config/logs"

SUBSYSTEMS: dict[str, dict] = {
    "fancoil": {
        "log_dir":            f"{BASE_LOG_DIR}/fancoil_events",
        "log_file":           "fancoil_events.log",
        "archive":            True,
        "archive_max_bytes":  5 * 1024 * 1024,   # 5 MB
        "state_persistence":  True,
    },
    "ev": {
        "log_dir":            f"{BASE_LOG_DIR}/EV",
        "log_file":           "ev_events.log",
        "archive":            False,
        "state_persistence":  False,
    },
    "scale": {
        "log_dir":            f"{BASE_LOG_DIR}/scale",
        "log_file":           "scale_events.log",
        "archive":            False,
        "state_persistence":  False,
    },
}

# ── Internal helpers ──────────────────────────────────────────────────────────

def _cfg(subsystem: str) -> dict:
    """Returns config for subsystem, falling back to sane defaults."""
    return SUBSYSTEMS.get(subsystem, {
        "log_dir":           f"{BASE_LOG_DIR}/{subsystem}",
        "log_file":          f"{subsystem}_events.log",
        "archive":           False,
        "state_persistence": False,
    })


def _log_path(subsystem: str) -> tuple[str, str]:
    cfg = _cfg(subsystem)
    log_dir = cfg["log_dir"]
    return log_dir, os.path.join(log_dir, cfg["log_file"])


def _state_file(subsystem: str) -> str:
    log_dir, _ = _log_path(subsystem)
    return os.path.join(log_dir, f"halog2026_{subsystem}_states.json")

# ── Public API ────────────────────────────────────────────────────────────────

def sync_write_log(subsystem: str, line: str) -> None:
    """Appends *line* to the subsystem log file, creating dirs as needed."""
    log_dir, log_file = _log_path(subsystem)
    try:
        os.makedirs(log_dir, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"[HALog2026] write_log [{subsystem}]: {e}")


def sync_archive_log(subsystem: str) -> None:
    """Rotates the log file when it exceeds archive_max_bytes (if enabled)."""
    cfg = _cfg(subsystem)
    if not cfg.get("archive"):
        return
    max_bytes = cfg.get("archive_max_bytes", 5 * 1024 * 1024)
    log_dir, log_file = _log_path(subsystem)
    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > max_bytes:
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            ts_str  = mtime.strftime("%Y-%m-%d_%H%M%S")
            base    = os.path.splitext(os.path.basename(log_file))[0]
            archived = os.path.join(log_dir, f"{base}_{ts_str}.log")
            os.rename(log_file, archived)
            print(f"[HALog2026] archived [{subsystem}] → {archived}")
    except Exception as e:
        print(f"[HALog2026] archive_log [{subsystem}]: {e}")


def sync_save_state(subsystem: str, entity_id: str, value: Any) -> None:
    """Persists a single entity value to the subsystem state JSON file."""
    sf      = _state_file(subsystem)
    log_dir = _log_path(subsystem)[0]
    try:
        os.makedirs(log_dir, exist_ok=True)
        data: dict = {}
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[entity_id] = value
        with open(sf, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[HALog2026] save_state [{subsystem}]: {e}")


def sync_read_states(subsystem: str) -> dict:
    """Returns the persisted entity map for *subsystem*, or {} on failure."""
    sf = _state_file(subsystem)
    try:
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[HALog2026] read_states [{subsystem}]: {e}")
    return {}
