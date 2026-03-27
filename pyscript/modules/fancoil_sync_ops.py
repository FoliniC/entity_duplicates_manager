import os
import json
from datetime import datetime

LOG_DIR = "/config/logs/fancoil_events"
LOG_FILE = f"{LOG_DIR}/fancoil_events.log"
STATE_FILE = f"{LOG_DIR}/fancoil_states.json"

def sync_archive_log():
    try:
        if os.path.exists(LOG_FILE):
            mtime = datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
            ts_str = mtime.strftime("%Y-%m-%d_%H%M%S")
            new_name = f"{LOG_DIR}/fancoil_events_{ts_str}.log"
            os.rename(LOG_FILE, new_name)
    except Exception as e:
        print(f"Archive error: {e}")

def sync_write_log(line):
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"Write log error: {e}")

def sync_save_state(entity_id, value):
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        states_data = {}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                states_data = json.load(f)
        states_data[entity_id] = value
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(states_data, f, indent=4)
    except Exception as e:
        print(f"Save state error: {e}")

def sync_read_states():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Read states error: {e}")
    return {}
