# Pyscript service with aiofiles for native async file operations
# Requires: pip install aiofiles

from datetime import datetime
import aiofiles

LOG_FILE = "/config/scale_events.log"

@service
async def scale_events_write(
    message: str = "",
    level: str = "INFO",
    action: str = "nulla",
    filename: str = LOG_FILE,
    append: bool = True,
    wait: int = 2,
):
    """
    Append a line to the scale events log file using aiofiles.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ritardo opzionale per permettere ai sensori di potenza di aggiornarsi
    if wait > 0:
        await task.sleep(wait)

    # Mappatura delle azioni
    action_map = {
        "acceso": "accensione",
        "spento": "spegnimento",
        "nulla": "invariato",
        "toggle": "toggle"
    }
    mapped_action = action_map.get(action, action)

    # Recupero potenza e stato luce
    try:
        p1 = float(state.get("sensor.sonoff_10024024c4_power_1") or 0)
        p2 = float(state.get("sensor.sonoff_10024024c4_power_2") or 0)
        power = p1 + p2
    except Exception:
        power = 0.0

    if power > 12:
        light_state = "ACCESA 💡"
    else:
        light_state = "SPENTA 🌑"

    # Format: TS [LEVEL] [ACTION] [LIGHT_STATE Power: X W] Message
    line = f"{ts} [{level}] [{mapped_action}] [Luce: {light_state} Power: {power:.2f}W] {message}\n"

    try:
        if append:
            async with aiofiles.open(filename, "a", encoding="utf-8") as f:
                await f.write(line)
        else:
            async with aiofiles.open(filename, "w", encoding="utf-8") as f:
                await f.write(line)

    except Exception as e:
        log.error(f"scale_events_write: failed to write to {filename}: {e}")