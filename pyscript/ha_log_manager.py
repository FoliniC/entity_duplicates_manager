# Pyscript service for managing Home Assistant core logs
# Archivia solo il log della sessione precedente al boot
import os
import shutil
import glob
from datetime import datetime

CONFIG_DIR = "/config"
LOG_DIR = os.path.join(CONFIG_DIR, "logs/ha")
OLD_LOG_DIR = os.path.join(LOG_DIR, "old")
OLD_LOG_FILE = os.path.join(CONFIG_DIR, "home-assistant.log.1")

@service
def ha_log_archive_previous():
    """Sposta home-assistant.log.1 nella cartella old con timestamp."""
    try:
        if not os.path.exists(OLD_LOG_DIR):
            os.makedirs(OLD_LOG_DIR)
            
        if os.path.exists(OLD_LOG_FILE):
            # Usiamo la data di ultima modifica del file per il timestamp
            mtime = datetime.fromtimestamp(os.path.getmtime(OLD_LOG_FILE))
            ts_str = mtime.strftime("%Y-%m-%d_%H%M%S")
            target_path = os.path.join(OLD_LOG_DIR, f"home-assistant_{ts_str}.log")
            
            shutil.move(OLD_LOG_FILE, target_path)
            log.info(f"Previous HA Session Log archived: {target_path}")

    except Exception as e:
        log.error(f"Error archiving old HA log: {e}")

@time_trigger("startup")
def startup_ha_log_manager():
    # All'avvio archiviamo il log della sessione precedente
    ha_log_archive_previous()
