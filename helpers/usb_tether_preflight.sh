#!/bin/bash
# Preflight "Normale": verifica il tethering Android sul router prima del cutover.
# In Intranet network.wan.auto=0 lascia usb0 DOWN anche con RNDIS Android attivo:
# il preflight misura Android, prova ifup wan SENZA rimuovere l'anchor Intranet,
# poi convalida il lease DHCP RNDIS ricevuto dal router.

set -u

LOG_FILE="/tmp/usb-tether-preflight.log"
ROUTER_KEY="/config/.ssh/router_key"
ROUTER_HOST="root@192.168.0.11"
SSH_CM_DIR="/config/.ssh/cm"
ANDROID_SERIAL="69a47f6d3a61"

mkdir -p "$SSH_CM_DIR" 2>/dev/null || true

ssh_router() {
    ssh -i "$ROUTER_KEY" \
        -o BatchMode=yes \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=8 \
        -o ControlMaster=auto \
        -o ControlPersist=60s \
        -o ControlPath="$SSH_CM_DIR/%C" \
        "$ROUTER_HOST" "$@"
}

log() { echo "[$(date -Iseconds)] PRE-FLIGHT: $*" >> "$LOG_FILE"; }

log "avvio verifica tethering Android + WAN router"

# Fonte primaria: stato USB Android. Non dipende da network.wan.auto del router.
PHONE_USB=$(ssh_router "/usr/bin/adb_router -s $ANDROID_SERIAL shell 'getprop sys.usb.config'" 2>&1)
PHONE_RC=$?
if [ "$PHONE_RC" -ne 0 ] || ! echo "$PHONE_USB" | grep -q 'rndis'; then
    SUMMARY=$(echo "$PHONE_USB" | head -2 | tr '\n' ' ')
    log "FAIL Android RNDIS non attivo o ADB assente: $SUMMARY"
    echo "Tethering Android non rilevato: ADB/RNDIS non attivo ($SUMMARY)"
    exit 1
fi

# In Intranet wan.auto=0: ifup wan promuove il lease usb0 senza rimuovere
# l'anchor br-lan metric 9. Il DHCP RNDIS può richiedere più di 5 secondi
# dopo un riavvio/riconnessione Android: attendiamo fino a 30s, invece di
# scambiare il normale stato transitorio IPv6-only per "tethering assente".
# MA serve auto=1 altrimenti ifup wan non negozia il lease.
ssh_router "uci set network.wan.auto='1'; uci commit network; /usr/bin/adb_router shell settings put global airplane_mode 0 >/dev/null 2>&1; /usr/bin/adb_router shell settings put global mobile_data 1 >/dev/null 2>&1; /usr/bin/adb_router shell svc data enable >/dev/null 2>&1; ifup wan >/dev/null 2>&1" >/dev/null 2>&1 || true

IP_INFO=""
IP_RC=1
for attempt in $(seq 1 30); do
    IP_INFO=$(ssh_router "ip -brief addr show usb0 2>/dev/null" 2>&1)
    IP_RC=$?
    IP_ADDR=$(echo "$IP_INFO" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]+' | cut -d/ -f1 | grep -v '^169\.254\.' | head -1)
    [ -n "$IP_ADDR" ] && break
    sleep 1
done

# Verifica generica: usb0 deve avere un IPv4 NON link-local (non 169.254.x.x, non fe80::)
# e un gateway raggiungibile via quell'interfaccia. Così si adatta a qualsiasi pool DHCP.
if [ "$IP_RC" -ne 0 ]; then
    IP_SUMMARY=$(echo "$IP_INFO" | head -3 | tr '\n' ' ')
    log "FAIL usb0 assente o errore: $IP_SUMMARY"
    echo "usb0 non trovato: $IP_SUMMARY"
    exit 1
fi

# Estrae il primo IPv4 non-link-local da usb0 (gia' raccolto nel ciclo DHCP sopra)
# Ripete l'estrazione per chiarezza e robustezza se il comando del ciclo cambia.
IP_ADDR=$(echo "$IP_INFO" | grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]+' | cut -d/ -f1 | grep -v '^169\.254\.' | head -1)
if [ -z "$IP_ADDR" ]; then
    IP_SUMMARY=$(echo "$IP_INFO" | head -3 | tr '\n' ' ')
    log "FAIL usb0 senza IPv4 valido (solo link-local?): $IP_SUMMARY"
    echo "usb0 senza lease IPv4 valido: $IP_SUMMARY"
    exit 1
fi

# Verifica che il gateway via usb0 risponda E che internet sia raggiungibile via usb0
# (il gateway potrebbe rispondere ma il NAT Android non instradare verso internet)
GW=$(ssh_router "ip route show dev usb0 2>/dev/null | awk '/^default/ {print \$3; exit}'" 2>&1)
if [ -z "$GW" ]; then
    log "FAIL gateway usb0 non trovato"
    echo "Gateway usb0 non trovato: lease presente ma nessuna route default"
    exit 1
fi

# Prima verifica che il gateway risponda (sanity check)
if ! ssh_router "ping -c 2 -W 3 -I usb0 $GW >/dev/null 2>&1"; then
    log "FAIL gateway usb0 non reachable: GW=$GW"
    echo "Gateway usb0 non raggiungibile (GW=$GW): lease presente ma tethering non instrada"
    exit 1
fi

# POI verifica connettività internet REALE via usb0 (non solo gateway)
# Questo coglie il caso "NAT Android desincronizzato" (RNDIS up ma niente internet)
if ! ssh_router "ping -c 2 -W 3 -I usb0 8.8.8.8 >/dev/null 2>&1 || ping -c 2 -W 3 -I usb0 1.1.1.1 >/dev/null 2>&1"; then
    log "FAIL internet non raggiungibile via usb0 (NAT Android desincronizzato): GW=$GW"
    echo "Internet non raggiungibile via usb0 (GW=$GW): tethering Android attivo ma NAT non instrada verso internet"
    exit 1
fi

log "OK Android RNDIS + usb0 lease $IP_ADDR, gateway $GW reachable"
echo "OK: tethering Android attivo; usb0 pronto (IP: $IP_ADDR, GW: $GW)"
exit 0