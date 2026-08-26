#!/bin/bash
# Safety watchdog for network state transitions

PREV_MODE="${1:-intranet}"
PREV_HOST="${2:-Debian (192.168.0.3)}"
TIMEOUT="${3:-35}"
LOG_FILE="/config/logs/usb_tether/usb_tether.log"
ERROR_MARKER="/config/logs/usb_tether/last_error.marker"

log_msg() {
    local lvl="$1"
    local msg="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$lvl] [FAILSAFE_WATCHDOG] $msg" >> "$LOG_FILE" 2>/dev/null || true
}

log_msg INFO "Watchdog avviato: in attesa di ${TIMEOUT}s per verificare la connettivita' (rollback di riserva: $PREV_MODE su $PREV_HOST)..."

sleep "$TIMEOUT"

# Test internet connectivity AFTER timeout
PING1_OUT=$(ping -c 2 -W 3 1.1.1.1 2>&1)
PING1_RC=$?

if [ $PING1_RC -eq 0 ]; then
    log_msg INFO "Watchdog disarmato: connettivita' internet VERIFICATA OK (1.1.1.1 raggiungibile) dopo il cambio stato."
    rm -f "$ERROR_MARKER" 2>/dev/null || true
    exit 0
fi

PING2_OUT=$(ping -c 2 -W 3 8.8.8.8 2>&1)
PING2_RC=$?

if [ $PING2_RC -eq 0 ]; then
    log_msg INFO "Watchdog disarmato: connettivita' internet VERIFICATA OK (8.8.8.8 raggiungibile) dopo il cambio stato."
    rm -f "$ERROR_MARKER" 2>/dev/null || true
    exit 0
fi

# Internet connection lost! Capture diagnostic details and timestamp
FAIL_TIME=$(date '+%H:%M:%S (%d/%m/%Y)')
DIAG_MSG="Internet ASSENTE dopo ${TIMEOUT}s (ping 1.1.1.1 e 8.8.8.8 falliti). Avvio rollback automatico verso $PREV_MODE"

log_msg ERROR "CRITICO: $DIAG_MSG | Output 1.1.1.1: $PING1_OUT | Output 8.8.8.8: $PING2_OUT"

# Write error marker file so HA sensor displays exact failure reason with timestamp
printf '%s\n%s\n' "$DIAG_MSG" "$FAIL_TIME" > "$ERROR_MARKER"

if [ "$PREV_MODE" = "intranet" ] || [ "$PREV_MODE" = "server" ]; then
    /config/helpers/usb_tether_ha.sh activate "$PREV_MODE" "$PREV_HOST" 60 1 >> "$LOG_FILE" 2>&1
else
    /config/helpers/usb_tether_ha.sh restore server "$PREV_HOST" 60 1 >> "$LOG_FILE" 2>&1
fi

log_msg INFO "Rollback di emergenza completato."
