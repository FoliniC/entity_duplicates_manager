#!/bin/bash
# reset_network.sh —Reset rete resiliente post-blackout / caso anomalo enp2s0
# Usa quando: dopo blackout, enp2s0 inutilizzabile, "PCI internet" come LAN,
# sia Normale che Intranet non funzionano, o quando lo stato tethering è bloccato.
# Log dettagliato delle funzionalità che falliscono (PITFALL 3/11/12).

set -u
LOG_DIR="/home/carlo/docker/homeassistant/config/logs/reset_network"
LOG_FILE="$LOG_DIR/reset_log_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR" || true

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" | tee -a "$LOG_FILE"
}

# --- Funzioni non funzionanti rilevate (user-report: blackout, enp2s0, PCI,L,N/I) ---
FAILURES=()

fail() {
    FAILURES+=("$1")
    log "FAIL: $1"
}

ok() {
    log "OK: $1"
}

# --- 1. Stato interfaccia LAN (enp2s0 / PCI / altro) ---
LAN_IF="enp2s0"
if [ ! -r "/sys/class/net/$LAN_IF/carrier" ]; then
    fail "LAN interfaccia $LAN_IF assente (post-blackout)"
else
    CARRIER=$(cat "/sys/class/net/$LAN_IF/carrier" 2>/dev/null || echo "0")
    if [ "$CARRIER" = "0" ]; then
        fail "LAN interfaccia $LAN_IF carrier=0 (cavo/spento)"
    else
        ok "LAN $LAN_IF carrier OK"
    fi
fi

# --- 2. Verifica se enp2s0 ha IP / se 'PCI internet' è impostato come connettività ---
# Se `nmcli` mostra la connessione attiva come 'PCI internet' (non la LAN corretta):
if command -v nmcli >/dev/null 2>&1; then
    ACTIVE_CONN=$(nmcli -t -f NAME,DEVICE,TYPE con show --active 2>/dev/null | grep -E 'PCI|internet|ethernet' | head -1 || true)
    if echo "$ACTIVE_CONN" | grep -qi 'pci\|internet'; then
        fail "Connessione attiva errata: '$ACTIVE_CONN' (dovrebbe essere LAN/enp2s0, non PCI/internet)"
    else
        ok "Connessione attiva: $ACTIVE_CONN"
    fi
fi

# --- 3. Ripristina NetworkManager sulla LAN corretto ---
# Se enp2s0 era su una connessione sbagliata, ricrea con IP statico persistente
if [ -d "/etc/NetworkManager/system-connections/" ]; then
    for f in /etc/NetworkManager/system-connections/*.nmconnection; do
        [ -f "$f" ] || continue
        NAME=$(basename "$f" .nmconnection)
        if echo "$NAME" | grep -qiE 'pci|internet'; then
            log "Rimuovo connessione sbagliata: $NAME"
            rm -f "$f" || fail "Non posso rimuovere connessione sbagliata $NAME"
        fi
    done
fi

# Creare/ripristinare connessione LAN persistente statico (come documentato RETE_LOCALE.md)
# IP 192.168.0.3/24, NO gateway (Debian esce via USB tethering, non router), DNS 192.168.0.11
NM_CONF="/etc/NetworkManager/system-connections/res1-enp2s0.nmconnection"
if [ ! -f "$NM_CONF" ]; then
    cat > "$NM_CONF" << 'NMEOF'
[connection]
id=res1-enp2s0
uuid=9a5e5ae8-07e3-4df5-bd6e-1a0f3f6a7b22
type=ethernet
interface-name=enp2s0

[ipv4]
method=manual
address1=192.168.0.3/24,192.168.0.11
# Nessun gateway: Debian esce via USB (tethering), non via router
# DNS del router (AdGuard) per la LAN
dns=192.168.0.11;

[ipv6]
method=ignore
NMEOF
    chmod 600 "$NM_CONF"
    ok "Creato NM_CONF $NM_CONF con IP statico 192.168.0.3/24, DNS 192.168.0.11"
fi

# --- 4. Riattiva connessione LAN ---
if nmcli con up res1-enp2s0 2>/dev/null; then
    ok "Retiattivato res1-enp2s0 via nmcli"
else
    fail "nmcli con up res1-enp2s0 fallito"
fi

# --- 5. Aggiungi default route Debian via USB tethering (se interfaccia USB presente) ---
# Se il telefono Note 13 Pro 5G è su Debian (enx...), aggiungi route metric 50.
USB_IFACE=$(ip -br link 2>/dev/null | grep -E '^enx' | awk '{print $1}' | head -1 || true)
if [ -n "$USB_IFACE" ]; then
    GW=$(get_default_gw 2>/dev/null || echo "10.87.160.73")
    # Prova a portare su interfaccia USB e aggiungere default route
    ip link set "$USB_IFACE" up 2>/dev/null || true
    ip route replace default via "$GW" dev "$USB_IFACE" metric 50 2>/dev/null || true
    if ip route show default 2>/dev/null | grep -q "dev $USB_IFACE"; then
        ok "Default route via USB $USB_IFACE ($GW) metric 50 attiva"
    else
        fail "Non riesco a impostare default route via $USB_IFACE"
    fi
else
    fail "Interfaccia USB tethering (enx*) assente su Debian"
fi

# --- 6. Router: verifica / ripristina WAN (usb0) se necessario ---
# Se router è ancora su Intranet (route via 192.168.0.3 metric 9) ma il telefono
# (Note 11) è sul router via USB, ridare la WAN.
# NOTE: StreamPack may keep usb0 UP as a local RNDIS link while Intranet is active;
# this check must not bring WAN up just because usb0 has an address.
ROUTER_IP="192.168.0.11"
ROUTER_KEY="/home/carlo/docker/homeassistant/config/.ssh/router_key"

if command -v ssh >/dev/null 2>&1 && [ -f "$ROUTER_KEY" ]; then
    ROUTE=$(ssh -i "$ROUTER_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@$ROUTER_IP "ip route show default 2>/dev/null | head -1" 2>/dev/null || true)
    if echo "$ROUTE" | grep -q 'dev usb0'; then
        ok "Router WAN attiva (usb0)"
    elif echo "$ROUTE" | grep -q 'dev br-lan'; then
        fail "Router ancora in Intranet (br-lan); WAN usb0 non attiva"
        # Ripristina la WAN rimuovendo la route Intranet residua e forzando l'ifup
        ssh -i "$ROUTER_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@$ROUTER_IP "
            uci set network.wan.auto='1';
            uci commit network 2>/dev/null;
            ip route del default via 192.168.0.3 dev br-lan metric 9 2>/dev/null || true;
            ifup wan 2>/dev/null;
            echo 'router WAN ripristinata (auto=1, route pulita, ifup wan)'"
        2>/dev/null || true
    else
        fail "Router senza default route ($ROUTE)"
    fi
else
    fail "Non posso raggiungere router via SSH ($ROUTER_IP)"
fi

# --- 7. Log delle funzionalità non funzionanti (per il futuro) ---
echo "--- RESUME FUNZIONALITÀ NON FUNZIONANTI ---" >> "$LOG_FILE"
# Legge FAILURES array
if [ ${#FAILURES[@]} -gt 0 ]; then
    for f in "${FAILURES[@]}"; do
        echo "BROKEN: $f" >> "$LOG_FILE"
    done
    echo "RESET_ESITO=FAIL (funzioni rotte: ${#FAILURES[@]})" >> "$LOG_FILE"
else
    echo "RESET_ESITO=OK (nessuna funzione rotta rilevata)" >> "$LOG_FILE"
fi
echo "LOG_FILE=$LOG_FILE" >> "$LOG_FILE"
echo "FINISCE reset alle $(date)" >> "$LOG_FILE"

echo "=== Reset completato ==="
echo "Log: $LOG_FILE"
echo "Funzioni rotte (${#FAILURES[@]}): ${FAILURES[*]:-nessuna}"
