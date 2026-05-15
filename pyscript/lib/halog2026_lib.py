"""
HALog2026 — Unified Home Assistant Logging Library
====================================================
Sync I/O layer: Advanced Rotation Engine with JSON Config.
Loads configuration from /config/logs/halog2026_config.json.
"""

import os
import sys
import json
import glob
from datetime import datetime
from typing import Any

# ── Configuration Defaults ───────────────────────────────────────────────────

JSON_CONFIG_PATH = "/config/logs/halog2026_config.json"
BASE_LOG_DIR = "/config/logs"
SUBSYSTEMS: dict[str, dict] = {}

# ── JSON Config Loader ───────────────────────────────────────────────────────

def load_config():
    """Loads configuration from JSON file, falling back to internal defaults."""
    global BASE_LOG_DIR, SUBSYSTEMS
    
    # Internal hardcoded fallbacks if JSON is missing
    default_subsystems = {
        "fancoil": {"log_dir": "/config/logs/fancoil_events", "log_file": "fancoil_events.log", "archive": True, "rotation_type": "both", "max_bytes": 5242880, "when": "midnight", "backup_count": 10, "state_persistence": True}
    }

    if not os.path.exists(JSON_CONFIG_PATH):
        print(f"[HALog2026] JSON config not found at {JSON_CONFIG_PATH}, using defaults")
        SUBSYSTEMS = default_subsystems
        return

    try:
        with open(JSON_CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            BASE_LOG_DIR = config_data.get("BASE_LOG_DIR", "/config/logs")
            SUBSYSTEMS = config_data.get("SUBSYSTEMS", default_subsystems)
            print(f"[HALog2026] Config loaded from JSON")
    except Exception as e:
        print(f"[HALog2026] Error reading JSON config: {e}")
        SUBSYSTEMS = default_subsystems

# Initial load
load_config()

# ── Internal helpers ──────────────────────────────────────────────────────────

def _cfg(subsystem: str) -> dict:
    return SUBSYSTEMS.get(subsystem, {
        "log_dir":           f"{BASE_LOG_DIR}/{subsystem}",
        "log_file":          f"{subsystem}_events.log",
        "archive":           False,
    })

def _log_path(subsystem: str) -> tuple[str, str]:
    cfg = _cfg(subsystem)
    log_dir = cfg["log_dir"]
    return log_dir, os.path.join(log_dir, cfg["log_file"])

def _should_rotate_time(log_file: str, when: str, interval: int = 1) -> bool:
    if not os.path.exists(log_file): return False
    mtime = os.path.getmtime(log_file)
    last_rot = datetime.fromtimestamp(mtime)
    now = datetime.now()
    
    if when == "midnight":
        return now.date() > last_rot.date()
    
    seconds_map = {"S": 1, "M": 60, "H": 3600, "D": 86400, "W": 604800}
    limit_seconds = seconds_map.get(when, 86400) * interval
    return (now - last_rot).total_seconds() > limit_seconds

# ── Public API ────────────────────────────────────────────────────────────────

def sync_write_log(subsystem: str, line: str) -> None:
    # Optional: reload config occasionally or on each write if performance allows
    # load_config() 
    log_dir, log_file = _log_path(subsystem)
    try:
        os.makedirs(log_dir, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"[HALog2026] write_log error: {e}")

def sync_archive_log(subsystem: str) -> None:
    """Professional Rotation Engine with Retention."""
    load_config() # Ensure we have latest settings before rotating
    cfg = _cfg(subsystem)
    if not cfg.get("archive"): return
    
    log_dir, log_file = _log_path(subsystem)
    if not os.path.exists(log_file): return

    r_type = cfg.get("rotation_type", "size")
    do_rotate = False

    if r_type in ["size", "both"]:
        if os.path.getsize(log_file) > cfg.get("max_bytes", 5242880):
            do_rotate = True
    
    if not do_rotate and r_type in ["time", "both"]:
        if _should_rotate_time(log_file, cfg.get("when", "D"), cfg.get("interval", 1)):
            do_rotate = True

    if do_rotate:
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        base = os.path.splitext(os.path.basename(log_file))[0]
        archived = os.path.join(log_dir, f"{base}_{ts}.log")
        try:
            os.rename(log_file, archived)
            print(f"[HALog2026] Rotated: {subsystem} -> {ts}")
        except Exception: pass

    backup_count = cfg.get("backup_count", 0)
    if backup_count > 0:
        base = os.path.splitext(os.path.basename(log_file))[0]
        archives = sorted(glob.glob(os.path.join(log_dir, f"{base}_*.log")), key=os.path.getmtime, reverse=True)
        if len(archives) > backup_count:
            for old_file in archives[backup_count:]:
                try: os.remove(old_file)
                except Exception: pass

def sync_save_state(subsystem: str, entity_id: str, value: Any) -> None:
    log_dir, _ = _log_path(subsystem)
    sf = os.path.join(log_dir, f"halog2026_{subsystem}_states.json")
    try:
        os.makedirs(log_dir, exist_ok=True)
        data = {}
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f: data = json.load(f)
        data[entity_id] = value
        with open(sf, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
    except Exception: pass

def sync_read_states(subsystem: str) -> dict:
    log_dir, _ = _log_path(subsystem)
    sf = os.path.join(log_dir, f"halog2026_{subsystem}_states.json")
    try:
        if os.path.exists(sf):
            with open(sf, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: pass
    return {}
