#!/bin/bash
# Preflight "normale": verifica USB tethering sul router prima di attivare NORMALE
# Se usb0 assente -> esce con rc=1, mantiene INTRANET (esce via br-lan)
set -u

LOG_FILE="/tmp/usb-tether-preflight.log"
SSH_CM_DIR="/config/.ssh/cm"
ROUTER_KEY="/config/.ssh/router_key"
ROUTER_HOST="root@192.168.0.11"

mkdir -p "$SSH_CM_DIR" 2>/dev/null || true

ssh_router() {
    ssh -i "$ROUTER_KEY" \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o LogLevel=QUIET \
        -o ConnectTimeout=5 \
        -o ControlMaster=auto \
        -o ControlPersist=60s \
        -o ControlPath="$SSH_CM_DIR/%C" \
        "$ROUTER_HOST" "$@"
}

echo "[$(date -Iseconds)] PRE-FLIGHT (normale): avvio verifica usb0 su router" >> "$LOG_FILE"

IP_INFO=$(ssh_router "ip -brief addr show usb0 2>/dev/null" 2>&1)
IP_RC=$?

if [ "$IP_RC" -ne 0 ] || ! echo "$IP_INFO" | grep -Eq '10.203.33.[0-9]+'; then
    IP_SUMMARY=$(echo "$IP_INFO" | head -3 | tr '\n' ' ')
    echo "[$(date -Iseconds)] PRE-FLIGHT FAIL: USB tethering assente (usb0). Mantengo INTRANET." >> "$LOG_FILE"
    echo "USB tethering assente su router (usb0 non rilevato o senza IP 10.203.33.x): $IP_SUMMARY"
    exit 1
fi

IP_ADDR=$(echo "$IP_INFO" | awk '{print $3}' | head -1)
echo "[$(date -Iseconds)] PRE-FLIGHT OK: usb0 attivo (IP: $IP_ADDR)" >> "$LOG_FILE"
echo "OK: usb0 attivo (IP: $IP_ADDR)"
exit 0
