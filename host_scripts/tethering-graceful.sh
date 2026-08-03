#!/bin/sh
# ============================================================================
# tethering-graceful.sh - transizione graduale del routing di default sul
# router OpenWrt, per non interrompere stream di lunga durata (es. radio via
# Alexa Echo) quando il router cambia backhaul internet (locale <-> anchor).
#
# Chiamato via SSH dal server Debian/Windows (root@router):
#   tethering-graceful.sh begin <table_id> <mark_hex> <device_ip> <old_gw> <old_dev> [snapshot_seconds]
#   tethering-graceful.sh end   <table_id> <mark_hex> [max_wait_seconds]
#
# 'begin' blocca per un tempo BREVE e fisso (snapshot_seconds, default 5s -
# niente a che vedere col drenaggio, che puo' durare ore): il tempo minimo
# per catturare le connessioni GIA' stabilite in quel momento. 'end' ritorna
# SUBITO: il drenaggio vero gira in un processo staccato (setsid), cosi' la
# sessione SSH che la invoca non resta appesa per ore.
#
# Prerequisiti (opkg):
#   opkg update && opkg install conntrack iptables-mod-conntrack-extra \
#       kmod-ipt-conntrack
#   which setsid   # se assente, vedi nota in fondo al file
#
# Bug evitati rispetto a un'implementazione "naturale" con CONNMARK:
#  1. "ip rule fwmark X lookup main" non ha ALCUN effetto se 'main' ha piu'
#     default route a metriche diverse: la scelta della rotta in una tabella
#     dipende solo dalla metrica, mai dal mark. Serve una tabella dedicata.
#  2. "CONNMARK --set-mark" da solo marca SOLO la connessione in conntrack,
#     mai il pacchetto: senza un "CONNMARK --restore-mark" a monte, "ip rule
#     fwmark" non scatta MAI (il meccanismo diventa un no-op silenzioso).
#  3. La tabella dedicata deve contenere ANCHE la subnet LAN come route
#     on-link: altrimenti il traffico di ritorno verso il device protetto
#     (che e' marcato, perche' appartiene alla stessa connessione) cadrebbe
#     sulla route di default della tabella e uscirebbe dall'interfaccia
#     sbagliata invece di essere consegnato direttamente sulla LAN.
#  4. La regola "set-mark ESTABLISHED,RELATED" NON puo' restare attiva per
#     tutta la durata del drenaggio (fino a ore): marcherebbe man mano anche
#     le connessioni NUOVE che nel frattempo diventano ESTABLISHED,
#     dirottandole per errore sul vecchio path. Va tenuta attiva solo per
#     una finestra breve ("snapshot" delle connessioni gia' in corso), poi
#     rimossa - restando solo "restore-mark" a propagare il mark gia' dato.
# ============================================================================

set -eu

LAN_NET="192.168.0.0/24"
LAN_DEV="br-lan"

ensure_chain() {
    # $1 = nome chain
    iptables -t mangle -N "$1" 2>/dev/null || true
    iptables -t mangle -C PREROUTING -j "$1" 2>/dev/null \
        || iptables -t mangle -A PREROUTING -j "$1"
}

case "${1:-}" in
  begin)
    TABLE_ID="$2"; MARK="$3"; DEV_IP="$4"; OLD_GW="$5"; OLD_DEV="$6"
    SNAPSHOT_SECONDS="${7:-5}"
    if [ -z "${OLD_GW:-}" ] || [ -z "${OLD_DEV:-}" ]; then
        echo "begin: old_gw/old_dev mancanti" >&2
        exit 1
    fi
    CHAIN="TETHER_${MARK}"

    ensure_chain "$CHAIN"
    iptables -t mangle -F "$CHAIN"

    # restore-mark: propaga il ct->mark gia' noto sul pacchetto, per TUTTA
    # la durata del drenaggio (necessario anche per i pacchetti successivi
    # delle connessioni marcate durante lo snapshot qui sotto).
    iptables -t mangle -A "$CHAIN" -j CONNMARK --restore-mark

    ip route add "$LAN_NET" dev "$LAN_DEV" table "$TABLE_ID" 2>/dev/null || true
    ip route replace default via "$OLD_GW" dev "$OLD_DEV" table "$TABLE_ID"
    ip rule del fwmark "$MARK" lookup "$TABLE_ID" 2>/dev/null || true
    ip rule add fwmark "$MARK" lookup "$TABLE_ID" pref 100

    # SNAPSHOT: marca le connessioni ESTABLISHED/RELATED del device protetto
    # SOLO per una finestra breve, poi rimuove questa regola specifica
    # (restore-mark sopra resta attivo e continua a proteggere chi e' stato
    # marcato qui). Senza questa rimozione, la regola resterebbe attiva per
    # tutto il drenaggio e "catturerebbe" anche connessioni nuove.
    iptables -t mangle -A "$CHAIN" -s "$DEV_IP" -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-mark "$MARK"
    sleep "$SNAPSHOT_SECONDS"
    iptables -t mangle -D "$CHAIN" -s "$DEV_IP" -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-mark "$MARK"

    echo "OK begin: table $TABLE_ID via $OLD_GW dev $OLD_DEV, mark $MARK, device $DEV_IP (snapshot ${SNAPSHOT_SECONDS}s)"
    ;;

  end)
    TABLE_ID="$2"; MARK="$3"; MAX_WAIT="${4:-21600}"   # tetto default 6h
    CHAIN="TETHER_${MARK}"

    DRAIN="/tmp/tethering-drain-${MARK}.sh"
    cat > "$DRAIN" <<EOF
#!/bin/sh
MARK_DEC=\$(( $MARK ))
WAITED=0
COUNT=1
while [ "\$WAITED" -lt "$MAX_WAIT" ]; do
    COUNT=\$(conntrack -L -m "\$MARK_DEC" 2>/dev/null | grep -Ec '^(tcp|udp|icmp|unknown|sctp)')
    [ "\$COUNT" -eq 0 ] && break
    sleep 20
    WAITED=\$((WAITED + 20))
done
iptables -t mangle -F "$CHAIN" 2>/dev/null || true
ip rule del fwmark "$MARK" lookup "$TABLE_ID" 2>/dev/null || true
ip route flush table "$TABLE_ID" 2>/dev/null || true
logger -t tethering-graceful "table $TABLE_ID (mark $MARK) ripulita dopo \${WAITED}s, flussi residui: \$COUNT"
rm -f "$DRAIN"
EOF
    chmod +x "$DRAIN"
    setsid "$DRAIN" >"/tmp/tethering-drain-${MARK}.log" 2>&1 < /dev/null &
    echo "OK end: drenaggio avviato in background (pid $!, tetto ${MAX_WAIT}s)"
    ;;

  *)
    echo "Uso: $0 {begin TABLE MARK IP OLD_GW OLD_DEV | end TABLE MARK [MAX_WAIT]}" >&2
    exit 1
    ;;
esac

# NOTA setsid: se il tuo build OpenWrt non lo include (raro, ma alcuni
# profili minimal lo escludono), verificalo con "which setsid" prima del
# primo uso reale. In assenza, sostituire la riga "setsid "$DRAIN" ..."
# con: ( "$DRAIN" >"/tmp/tethering-drain-${MARK}.log" 2>&1 < /dev/null & )
# disown 2>/dev/null - un po' meno robusto ma funzionante sulla maggior
# parte delle ash/busybox di OpenWrt.
