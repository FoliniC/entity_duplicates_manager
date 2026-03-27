# Pyscript service for logging
import sys
import os

# Ensure lib path is in sys.path - use absolute path standard for HA
LIB_PATH = "/config/pyscript/lib"
if LIB_PATH not in sys.path:
    sys.path.append(LIB_PATH)

try:
    import fancoil_lib
    # log.info("Pyscript fancoil_events_write: Successfully imported fancoil_lib")
except ImportError:
    # Fallback for different environments
    LIB_PATH_ALT = "./pyscript/lib"
    if LIB_PATH_ALT not in sys.path:
        sys.path.append(LIB_PATH_ALT)
    import fancoil_lib

@service
def fancoil_events_write(message="", level="INFO"):
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Assicuro che ci sia un newline finale e trimmo spazi superflui
    msg_clean = message.strip()
    lvl_upper = level.upper()
    line = f"{ts} [{lvl_upper}] {msg_clean}\n"
    task.executor(fancoil_lib.sync_write_log, line)

@service
def fancoil_flush_boot_buffer(entity_id=None):
    """Scrive il buffer pre-formattato direttamente sul file di log, gestendo i placeholder."""
    if not entity_id:
        return
    
    try:
        raw_content = state.getattr(entity_id).get("log_queue", "")
        if not raw_content:
            return
        
        # Sostituisco il placeholder con newline Unix
        buffer_content = raw_content.replace("[[BR]]", "\n")
        
        # Debug print
        print(f"DEBUG fancoil_flush_boot_buffer: content length {len(buffer_content)}")
        
        # Scrivo l'intero blocco
        task.executor(fancoil_lib.sync_write_log, "\n" + buffer_content)
        
        num_lines = buffer_content.count('\n')
        fancoil_events_write(f"Svuotato buffer di boot ({num_lines} messaggi)", "SYSTEM")
        
    except Exception as e:
        fancoil_events_write(f"Errore nel flush del buffer: {e}", "ERROR")

@service
def fancoil_state_save(entity_id=None, value=None):
    if not entity_id: return
    task.executor(fancoil_lib.sync_save_state, entity_id, value)

@service
def fancoil_states_restore():
    states_data = task.executor(fancoil_lib.sync_read_states)
    if not states_data: return
    for entity_id, value in states_data.items():
        domain = entity_id.split(".")[0]
        try:
            if domain == "input_number":
                input_number.set_value(entity_id=entity_id, value=float(value))
            elif domain == "input_boolean":
                if value in ["on", "True", True]:
                    input_boolean.turn_on(entity_id=entity_id)
                else:
                    input_boolean.turn_off(entity_id=entity_id)
        except Exception: pass
    fancoil_events_write("Ripristino stati da file completato", "SYSTEM")

@time_trigger("startup")
def startup_logic():
    task.executor(fancoil_lib.sync_archive_log)
    from datetime import datetime
    now_str = datetime.now().strftime("%H:%M:%S")
    # In pyscript, accessing state.sensor_uptime directly or via get
    try:
        uptime = state.get("sensor.uptime")
    except:
        uptime = "unknown"
    msg = f"=== Home Assistant / Pyscript started (New Log Session) | Time: {now_str} | Uptime: {uptime} ==="
    fancoil_events_write(msg + "\n", "SYSTEM")
    # Specchia l'avvio sessione nel log di sistema di HA
    system_log.write(level="info", logger="fancoil_system", message=msg)

    # Flush buffer and disable buffering mode
    fancoil_flush_boot_buffer(entity_id="input_boolean.fancoil_boot_buffering")
    input_boolean.turn_off(entity_id="input_boolean.fancoil_boot_buffering")
    # Reset room semaphore
    input_text.set_value(entity_id="input_text.fancoil_boot_semaphore", value="none")