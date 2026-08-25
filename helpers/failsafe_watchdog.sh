#!/bin/bash
# Safety watchdog for network state transitions

PREV_MODE="${1:-intranet}"
PREV_HOST="${2:-Debian (192.168.0.3)}"
TIMEOUT="${3:-35}"
LOG_FILE="/config/logs/usb_tether/usb_tether.log"

log_msg() {
    local lvl="$1"
    local msg="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$lvl] [FAILSAFE_WATCHDOG] $msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_msg INFO "Watchdog avviato: in attesa di ${TIMEOUT}s per verificare la connettivita' (rollback di riserva: $PREV_MODE su $PREV_HOST)..."

sleep "$TIMEOUT"

# Test internet connectivity AFTER timeout
if ping -c 2 -W 3 1.1.1.1 >/dev/null 2>&1 || ping -c 2 -W 3 8.8.8.8 >/dev/null 2>&1; then
    log_msg INFO "Watchdog disarmato: connettivita' internet VERIFICATA OK dopo il cambio stato."
    exit 0
fi

# Internet connection lost! Auto-rollback to previous working mode
log_msg ERROR "CRITICO: Connessione Internet FALLITA dopo ${TIMEOUT}s! Avvio rollback automatico verso $PREV_MODE su $PREV_HOST"

if [ "$PREV_MODE" = "intranet" ] || [ "$PREV_MODE" = "server" ]; then
    /config/helpers/usb_tether_ha.sh activate "$PREV_MODE" "$PREV_HOST" 60 >> "$LOG_FILE" 2>&1
else
    /config/helpers/usb_tether_ha.sh restore server "$PREV_HOST" 60 >> "$LOG_FILE" 2>&1
fi

log_msg INFO "Rollback di emergenza completato con successo."
