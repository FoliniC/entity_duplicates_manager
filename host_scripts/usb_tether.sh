#!/bin/bash
# ============================================================================
# usb_tether.sh - Gestione tethering USB come default route temporanea
# ----------------------------------------------------------------------------
# Permette di instradare temporaneamente il traffico Internet del server Debian
# verso un telefono collegato in USB tethering, mantenendo intatta la LAN.
# Pensato per aggiornamenti software (apt) pagati con i giga del cellulare.
#
# Estensione: abilita NAT/forwarding per traffico router (192.168.0.11) via server
# quando il tethering è attivo. Il router usa la route metric 30 come fallback.
#
# Modello di sicurezza:
#   - Lo swap di route e' NON persistente (modifica runtime, niente config NM).
#   - Lo stato vive in /run (tmpfs): al reboot tutto torna normale (auto-heal).
#   - Un watcher detached garantisce il ripristino anche se HA/SSH cadono.
#   - Tutto gira come root via un'unica regola sudoers NOPASSWD scoped.
#
# Uso (via sudo):
#   usb_tether.sh detect               -> stampa IFACE|GW o riga vuota
#   usb_tether.sh activate <max_min> [intranet|server] -> attiva route + watcher (default 30')
#   usb_tether.sh restore              -> ripristina (idempotente, sicura a idle)
#   usb_tether.sh status               -> JSON stato (active/idle/error)
#   usb_tether.sh _watch <expire_at>   -> interno: loop del watcher
# ============================================================================

set -u

# --- Costanti ---
STATE_FILE="/run/usb_tether_state"
PID_FILE="/run/usb_tether_watcher.pid"
LAN_NET="192.168.0.0/24"
LAN_IF="enp2s0"                       # interfaccia LAN del server
ROUTER_IP="192.168.0.11"              # IP router OpenWrt (sorgente traffico da NATare)
ROUTER_SSH_KEY="/home/carlo/docker/homeassistant/config/.ssh/router_key"
ROUTER_ROUTE_METRIC=30                # metric della route sul router (dopo wan=10, wwan=20)
ROUTER_WAN_IF="usb0"                  # interfaccia WAN USB del router OpenWrt
# Pattern di interfacce da ESCLUDERE nella ricerca del telefono.
# Le veth hanno suffisso @ifN (es. vethabc123@if2) che va gestito.
EXCLUDE_RE='^(lo|docker[0-9]*|br-[a-f0-9]+|veth[a-f0-9]+(@.*)?|zt[a-z0-9]+|tun[0-9]*|enp2s0|sit[0-9]*|ip6tnl[0-9]*|wlan[0-9]+)$'

# --- Utility ---
now_epoch() { date +%s; }
now_iso()   { date '+%Y-%m-%d %H:%M:%S'; }

# Escapa una stringa per JSON (limitato ma sufficiente per i nostri dati).
json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    printf '%s' "$s"
}

# --- SSH Router ---
# Esegue comando SSH sul router OpenWrt (non interattivo, timeout breve).
router_ssh() {
    ssh -i "$ROUTER_SSH_KEY" \
        -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=5 -o BatchMode=yes \
        root@"$ROUTER_IP" "$@" 2>/dev/null
}

# Aggiunge/rimuove la route di default sul router via server (metric 30).
router_add_fallback_route() {
    router_ssh "ip route replace default via 192.168.0.3 dev br-lan metric $ROUTER_ROUTE_METRIC" \
        && echo "Route fallback aggiunta sul router (metric $ROUTER_ROUTE_METRIC)." \
        || echo "WARN: impossibile aggiungere route fallback sul router." >&2
}

router_del_fallback_route() {
    router_ssh "ip route del default via 192.168.0.3 dev br-lan metric $ROUTER_ROUTE_METRIC 2>/dev/null; true" \
        && echo "Route fallback rimossa dal router." \
        || echo "WARN: impossibile rimuovere route fallback dal router (forse gia assente)." >&2
}

# Legge da netifd il gateway DHCP attuale della WAN USB del router.
router_wan_gateway() {
    router_ssh "ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1" \
        | tr -d '\r'
}

# Toglie/ripristina la WAN primaria del router per forzare tutto il traffico via server.
router_wan_down() {
    router_ssh "while ip route del default dev $ROUTER_WAN_IF metric 10 2>/dev/null; do :; done; true" \
        && echo "WAN router disattivata (route $ROUTER_WAN_IF rimossa)." \
        || echo "WARN: WAN router gia assente o errore." >&2
}

router_wan_up() {
    local gw
    gw=$(router_wan_gateway | head -1)
    if [[ "$gw" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        router_ssh "ip route replace default via $gw dev $ROUTER_WAN_IF metric 10 2>/dev/null; true" \
            && echo "WAN router riattivata (route $ROUTER_WAN_IF via $gw ripristinata)." \
            || echo "WARN: impossibile ripristinare WAN router." >&2
    else
        router_ssh "ifup wan >/dev/null 2>&1; sleep 2; GW=\$(ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1); [ -n \"\$GW\" ] && ip route replace default via \"\$GW\" dev $ROUTER_WAN_IF metric 10 2>/dev/null; true" \
            && echo "WAN router riattivata tramite ifup wan." \
            || echo "WARN: impossibile ripristinare WAN router." >&2
    fi
}

# --- NAT/Forwarding per traffico LAN router -> telefono ---
# Abilita IP forwarding e MASQUERADE per tutto il traffico LAN (192.168.0.0/24)
# che arriva al server e deve uscire dall'interfaccia telefono.
# NOTA: il router NON fa NAT su br-lan (interfaccia LAN), quindi i pacchetti
# arrivano al server con IP originale dei dispositivi (es. 192.168.0.8).
# MASQUERADE copre tutto il subnet LAN, non solo l'IP del router.
enable_nat_router() {
    local phone_if="$1"
    # 1) Abilita forwarding (idempotente).
    sysctl -w net.ipv4.ip_forward=1 >/dev/null
    # 2) MASQUERADE per TUTTO il traffico LAN diretto al telefono.
    #    Usa commento per renderla identificabile/rimovibile.
    iptables -t nat -C POSTROUTING -s "$LAN_NET" -o "$phone_if" \
        -m comment --comment "usb_tether_router_nat" -j MASQUERADE 2>/dev/null \
        || iptables -t nat -A POSTROUTING -s "$LAN_NET" -o "$phone_if" \
            -m comment --comment "usb_tether_router_nat" -j MASQUERADE
    # 3) Forwarding esplicito per tutto il subnet LAN (policy default potrebbe essere DROP).
    iptables -C FORWARD -s "$LAN_NET" -o "$phone_if" \
        -m comment --comment "usb_tether_router_fwd" -j ACCEPT 2>/dev/null \
        || iptables -A FORWARD -s "$LAN_NET" -o "$phone_if" \
            -m comment --comment "usb_tether_router_fwd" -j ACCEPT
    iptables -C FORWARD -d "$LAN_NET" -i "$phone_if" \
        -m comment --comment "usb_tether_router_fwd" -j ACCEPT 2>/dev/null \
        || iptables -A FORWARD -d "$LAN_NET" -i "$phone_if" \
            -m comment --comment "usb_tether_router_fwd" -j ACCEPT
    # 4) Aggiungi default route sul router via server (metric alta = fallback).
    router_add_fallback_route
    echo "NAT/forwarding per LAN abilitato su $phone_if."
}

disable_nat_router() {
    local phone_if="$1"
    # 1) Rimuovi regole iptables (per commento, indipendente da interfaccia attuale).
    iptables -t nat -D POSTROUTING -m comment --comment "usb_tether_router_nat" -j MASQUERADE 2>/dev/null || true
    iptables -D FORWARD -m comment --comment "usb_tether_router_fwd" -j ACCEPT 2>/dev/null || true
    # 2) Rimuovi route default sul router via server.
    router_del_fallback_route
    # 3) Non disabilitiamo ip_forward globalmente (potrebbe servire ad altro).
    echo "NAT/forwarding per router disabilitato."
}

# Restituisce il gateway di default attuale (metrica minore, escluso telefono).
# Cerca la default route NON associata a /dev $phone_if (gestito dal chiamante).
get_default_gw() {
    ip route show default 2>/dev/null \
        | awk '{ for(i=1;i<=NF;i++){ if($i=="via"){print $(i+1); exit} } }' \
        | head -1
}

# --- get_iface_gateway ------------------------------------------------------
# Restituisce il gateway IPv4 di un'interfaccia tethering attiva. Prova, in ordine:
#   1) la default route sull'interfaccia (caso normale);
#   2) IP4.GATEWAY di NetworkManager (mai vuoto se il telefono lo fornisce);
#   3) qualsiasi hop "via" di una route sull'interfaccia;
#   4) IP4.DNS[1] di NM — MOLTI telefoni (Xiaomi in primis) omettono l'opzione
#      DHCP 'router' ma forniscono il DNS, che nel tethering coincide col
#      gateway (il telefono stesso fa DHCP+DNS+NAT sullo stesso IP).
#      Validato con un ping: un gateway deve rispondere.
# Arg: $1 = nome interfaccia. Stampa il GW o vuoto.
get_iface_gateway() {
    local iface="$1" gw=""
    # 1) default route sull'interfaccia.
    gw=$(ip route show dev "$iface" 2>/dev/null \
         | awk '{ if($1=="default"){ for(i=1;i<=NF;i++){ if($i=="via"){print $(i+1); exit} } } }' \
         | head -1)
    [ -n "$gw" ] && { printf '%s' "$gw"; return 0; }

    # 2) NetworkManager IP4.GATEWAY per il device.
    if command -v nmcli >/dev/null 2>&1; then
        gw=$(nmcli -t -f IP4.GATEWAY dev show "$iface" 2>/dev/null | cut -d: -f2 | head -1)
        [ -n "$gw" ] && { printf '%s' "$gw"; return 0; }
    fi

    # 3) qualsiasi hop "via" sull'interfaccia.
    gw=$(ip route show dev "$iface" 2>/dev/null \
         | awk '{ for(i=1;i<=NF;i++){ if($i=="via"){print $(i+1); exit} } }' \
         | head -1)
    [ -n "$gw" ] && { printf '%s' "$gw"; return 0; }

    # 4) Fallback DNS: telefoni senza opzione DHCP 'router'. Il DNS e' quasi
    #    sempre il telefono-gateway. Verifichiamo con un ping (3 pacchetti,
    #    1s l'uno): se risponde, lo usiamo.
    if command -v nmcli >/dev/null 2>&1; then
        local dns
        dns=$(nmcli -t -f IP4.DNS dev show "$iface" 2>/dev/null | cut -d: -f2 | head -1)
        if [ -n "$dns" ]; then
            if ping -c 3 -W 1 "$dns" >/dev/null 2>&1; then
                printf '%s' "$dns"
                return 0
            fi
        fi
    fi
}

# --- bring_up_iface ---------------------------------------------------------
# Porta UP un'interfaccia USB e ottiene un lease DHCP dal telefono via
# NetworkManager (l'host non ha client DHCP standalone: dhclient/udhcpc/dhcpcd
# sono tutti assenti; NM e' il solo gestore di rete).
#
# Strategia NON persistente: crea una connessione NM temporanea con
# autoconnect=no (cosi' NON si riattiva da sola al reboot) + senza default route
# (la aggiungeremo noi manualmente con metric 50). Al restore la connessione
# viene cancellata, lasciando NM pulito come prima.
#
# Arg: $1 = nome interfaccia. Ritorna 0 se l'interfaccia ha un IPv4.
bring_up_iface() {
    local iface="$1"
    [ -n "$iface" ] || return 1

    # Gia' attiva con un IPv4? Niente da fare.
    ip -4 addr show dev "$iface" 2>/dev/null | grep -q 'inet ' && return 0

    # Richiede nmcli (presente su tutti i sistemi con NetworkManager).
    command -v nmcli >/dev/null 2>&1 || return 1

    # Crea connessione temporanea: DHCP, autoconnect=no (no riattivazione reboot),
    # never-default=yes (NM NON aggiunge la default route: la gestiamo noi con
    # metric 50 cosi' la LAN resta preferita quando il tethering e' off).
    # --nome univoco derivato dall'interfaccia, per cleanup affidabile.
    local conn_name="usb-tether-${iface}"
    nmcli con add type ethernet ifname "$iface" con-name "$conn_name" \
        ipv4.method auto ipv6.method ignore \
        connection.autoconnect no \
        ipv4.never-default yes >/dev/null 2>&1 || true

    # Attiva la connessione (NM ottiene IP via DHCP interno). Timeout ~30s.
    timeout 30 nmcli con up "$conn_name" >/dev/null 2>&1 || true

    sleep 1
    ip -4 addr show dev "$iface" 2>/dev/null | grep -q 'inet '
}

# --- tear_down_iface --------------------------------------------------------
# Rimuove la connessione NM temporanea creata da bring_up_iface.
# Idempotente. Arg: $1 = nome interfaccia.
tear_down_iface() {
    local iface="$1"
    [ -n "$iface" ] || return 0
    local conn_name="usb-tether-${iface}"
    nmcli con delete "$conn_name" >/dev/null 2>&1 || true
    nmcli dev disconnect "$iface" >/dev/null 2>&1 || true
}

# --- detect -----------------------------------------------------------------
# Trova l'interfaccia tethering: UP, con IPv4, gateway fuori dalla LAN.
# Se trova un'interfaccia con carrier ma senza IP/gateway, prova a portarla UP
# via DHCP (vedi bring_up_iface). Stampa "IFACE|GW" o riga vuota (exit 1).
cmd_detect() {
    local iface gw carrier brought_up=""
    # ip -br link mostra: IFACE STATUS ...
    while read -r iface _rest; do
        [ -z "$iface" ] && continue
        [[ "$iface" =~ $EXCLUDE_RE ]] && continue

        # Deve avere carrier (cavo collegato, telefono attivo).
        [ -r "/sys/class/net/$iface/carrier" ] || continue
        carrier=$(cat "/sys/class/net/$iface/carrier" 2>/dev/null)
        [ "$carrier" = "1" ] || continue

        # Se non ha IPv4, prova a portarla UP via DHCP (una sola volta per chiamata).
        if ! ip -4 addr show dev "$iface" 2>/dev/null | grep -q 'inet '; then
            # Evita loop: attiva solo la prima interfaccia candidata priva di IP.
            if [ -z "$brought_up" ]; then
                bring_up_iface "$iface" || true
                brought_up="$iface"
            else
                continue
            fi
        fi
        # Ora deve avere un IPv4.
        ip -4 addr show dev "$iface" 2>/dev/null | grep -q 'inet ' || continue

        # Gateway: usa l'helper (route o, se never-default, IP4.GATEWAY di NM).
        gw=$(get_iface_gateway "$iface")
        [ -z "$gw" ] && continue

        # Il gateway del telefono NON deve stare nella LAN (192.168.0.0/24).
        # I telefoni tipicamente usano 192.168.42.x o simili.
        if ip route get "$gw" >/dev/null 2>&1; then
            printf '%s|%s\n' "$iface" "$gw"
            return 0
        fi
    done < <(ip -br link 2>/dev/null)
    return 1
}

# --- activate ---------------------------------------------------------------
# Salva stato, aggiunge default route (metric 50) e lancia il watcher.
# Se il secondo argomento e' "intranet", disabilita anche la WAN del router
# per dirottare tutto il traffico LAN via server.
cmd_activate() {
    local max_min="${1:-30}" mode="${2:-server}"
    # Validazione durata.
    case "$max_min" in
        ''|*[!0-9]*) max_min=30 ;;
    esac
    [ "$max_min" -lt 1 ] 2>/dev/null && max_min=1
    [ "$max_min" -gt 480 ] 2>/dev/null && max_min=480

    # Gia' attivo? Rifiuta (evita doppi swap). Ha senso solo se lo stato e' coerente.
    if [ -f "$STATE_FILE" ]; then
        local cur_state
        cur_state=$(grep -E '^state=' "$STATE_FILE" 2>/dev/null | cut -d= -f2-)
        if [ "$cur_state" = "active" ]; then
            echo "GIA ATTIVO: usa 'restore' prima di riattivare." >&2
            return 1
        fi
    fi

    # Rileva il telefono.
    local det iface gw
    det=$(cmd_detect) || true
    if [ -z "$det" ]; then
        echo "Telefono USB non rilevato. Attiva il tethering sul cellulare e collega il cavo USB." >&2
        return 2
    fi
    iface="${det%%|*}"
    gw="${det#*|}"

    # Gateway LAN originale = default route attuale (prima di aggiungere quella del telefono).
    local lan_gw
    lan_gw=$(get_default_gw)
    [ -z "$lan_gw" ] && lan_gw="192.168.0.11"   # fallback noto dalla documentazione

    local now expire
    now=$(now_epoch)
    expire=$((now + max_min * 60))

    # Aggiungi la default route via telefono con metrica PIU BASSA (vince).
    # Non tocchiamo la route LAN esistente: resta a metric 100.
    if ! ip route add default via "$gw" dev "$iface" metric 50 2>/dev/null; then
        # Se esiste gia' una route identica, sostituiscila.
        ip route replace default via "$gw" dev "$iface" metric 50 2>/dev/null || {
            echo "Impossibile aggiungere la route via $iface." >&2
            return 3
        }
    fi

    # Abilita NAT/forwarding per traffico router -> telefono.
    enable_nat_router "$iface"

    # Se modalita' "intranet", disabilita anche la WAN del router,
    # cosi' tutto il traffico LAN passa forzatamente via server.
    local intranet_mode="false"
    if [ "$mode" = "intranet" ]; then
        router_wan_down
        intranet_mode="true"
        echo "Modalita' INTRANET: WAN router disattivata, traffico LAN forzato via $iface."
    fi

    # Salva stato (include la modalita' per ripristino corretto).
    {
        echo "state=active"
        echo "mode=$mode"
        echo "phone_if=$iface"
        echo "phone_gw=$gw"
        echo "lan_gw=$lan_gw"
        echo "activated_at=$now"
        echo "expire_at=$expire"
    } > "$STATE_FILE"

    # Lancia il watcher detached: fa da safety net indipendente da HA.
    # Il watcher dorme e poi chiama restore; viene killato se si fa restore manuale.
    if [ -f "$PID_FILE" ]; then
        kill "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    setsid bash "$0" _watch "$expire" >/dev/null 2>&1 < /dev/null &
    echo $! > "$PID_FILE"

    echo "OK attivato: $iface via $gw per ${max_min} min (modalita $mode)."
    return 0
}

# --- restore ----------------------------------------------------------------
# Idempotente: rimuove la route del telefono, killa il watcher, cancella stato.
cmd_restore() {
    local phone_if="" phone_gw=""

    # Killa sempre il watcher se presente.
    if [ -f "$PID_FILE" ]; then
        local wpid
        wpid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$wpid" ]; then
            # killa l'intero processo+figli (il watcher e' in setsid).
            kill -- "-$wpid" 2>/dev/null || kill "$wpid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi

    # Rimuovi la route del telefono se presente nello stato o a runtime.
    if [ -f "$STATE_FILE" ]; then
        phone_if=$(grep -E '^phone_if=' "$STATE_FILE" | cut -d= -f2-)
        phone_gw=$(grep -E '^phone_gw=' "$STATE_FILE" | cut -d= -f2-)
    fi
    # Tentativo basato sullo stato.
    if [ -n "$phone_if" ] && [ -n "$phone_gw" ]; then
        ip route del default via "$phone_gw" dev "$phone_if" metric 50 2>/dev/null || true
    fi
    # Tentativo generico: rimuovi ogni default route con metric 50 (la nostra firma).
    while ip route del default metric 50 2>/dev/null; do :; done

    # Rimuovi la connessione NM temporanea creata da bring_up_iface, se presente.
    if [ -n "$phone_if" ]; then
        tear_down_iface "$phone_if"
    fi

    # Disabilita NAT/forwarding per traffico router.
    disable_nat_router "$phone_if"

    # Ripristina la WAN del router (sempre, per sicurezza).
    router_wan_up

    rm -f "$STATE_FILE"
    echo "OK ripristinato: default route tornata alla LAN."
    return 0
}

# --- _watch (interno) -------------------------------------------------------
# Loop del watcher: aspetta expire_at poi restore. Esce se restore esterno.
cmd_watch() {
    local expire="$1"
    # Poll ogni 15s: se scaduto, restore; se lo stato e' sparito, esci.
    while true; do
        local now
        now=$(now_epoch)
        if [ "$now" -ge "$expire" ]; then
            cmd_restore >/dev/null 2>&1
            exit 0
        fi
        # Se lo stato e' stato rimosso da un restore manuale, esci silenziosamente.
        [ -f "$STATE_FILE" ] || exit 0
        sleep 15
    done
}

# --- status -----------------------------------------------------------------
# Stampa JSON con stato + attributi. E' la fonte di verita' per HA.
cmd_status() {
    local state="idle" mode="server" phone_if="" phone_gw="" lan_gw="" active_since="" remaining_min=0 auto_expire="false" message="Inattivo"
    local now
    now=$(now_epoch)

    if [ -f "$STATE_FILE" ]; then
        state=$(grep -E '^state=' "$STATE_FILE" | cut -d= -f2-)
        mode=$(grep -E '^mode=' "$STATE_FILE" | cut -d= -f2-)
        phone_if=$(grep -E '^phone_if=' "$STATE_FILE" | cut -d= -f2-)
        phone_gw=$(grep -E '^phone_gw=' "$STATE_FILE" | cut -d= -f2-)
        lan_gw=$(grep -E '^lan_gw=' "$STATE_FILE" | cut -d= -f2-)
        active_since=$(grep -E '^activated_at=' "$STATE_FILE" | cut -d= -f2-)
        local expire
        expire=$(grep -E '^expire_at=' "$STATE_FILE" | cut -d= -f2-)
        if [ -n "$expire" ] && [ -n "$active_since" ]; then
            remaining_min=$(( (expire - now) / 60 ))
            [ "$remaining_min" -lt 0 ] && remaining_min=0
            auto_expire="true"
        fi
        # Coerenza: lo stato dice active ma la route non c'e' piu' (es. reboot parziale)?
        if [ "$state" = "active" ]; then
            if ! ip route show default metric 50 >/dev/null 2>&1 \
               || [ -z "$(ip route show default metric 50 2>/dev/null)" ]; then
                state="error"
                message="Stato attivo ma route telefonica assente: eseguire restore."
            else
                message="Attivo via ${phone_if}"
            fi
        fi
    fi

    # Formatta active_since in formato leggibile.
    local since_human=""
    if [ -n "$active_since" ] && [ "$active_since" != "0" ]; then
        since_human=$(date -d "@$active_since" '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
    fi

    cat <<EOF
{"state":"$state","mode":"$mode","phone_if":"$(json_escape "$phone_if")","phone_gw":"$(json_escape "$phone_gw")","lan_gw":"$(json_escape "$lan_gw")","active_since":"$(json_escape "$since_human")","remaining_min":$remaining_min,"auto_expire":$auto_expire,"message":"$(json_escape "$message")"}
EOF
}

# --- diagnose (solo troubleshooting, output testuale) -----------------------
# Mostra lo stato di tutte le interfacce candidate e prova manualmente il
# bring-up NM, cosi' si vede dove si blocca. Non modifica route ne' stato.
cmd_diagnose() {
    local iface carrier has_ip
    echo "=== Interfacce di rete (escluse virtuali/LAN) ==="
    while read -r iface _rest; do
        [ -z "$iface" ] && continue
        [[ "$iface" =~ $EXCLUDE_RE ]] && continue
        carrier=$(cat "/sys/class/net/$iface/carrier" 2>/dev/null)
        if ip -4 addr show dev "$iface" 2>/dev/null | grep -q 'inet '; then has_ip="SI"; else has_ip="NO"; fi
        printf '  %-18s carrier=%s ipv4=%s\n' "$iface" "${carrier:-?}" "$has_ip"
    done < <(ip -br link 2>/dev/null)

    echo
    echo "=== Stato dispositivi NetworkManager ==="
    nmcli dev status 2>/dev/null | grep -vE '^lo '

    echo
    echo "=== lsusb (telefono presente?) ==="
    lsusb 2>/dev/null | grep -iE 'xiaomi|motorola|samsung|apple|oneplus|google|huawei|oppo|realme|honor| rndis' || echo "  (nessun telefono noto rilevato)"

    echo
    echo "=== Connessioni NM esistenti usb-tether-* ==="
    nmcli -t -f NAME con show 2>/dev/null | grep -i 'usb-tether' || echo "  (nessuna)"

    echo
    echo "=== Moduli kernel USB-net caricati ==="
    lsmod 2>/dev/null | grep -iE 'rndis|cdc_ether|cdc_ncm|ax88179' || echo "  (nessun modulo USB-net caricato - potrebbe essere il problema)"

    echo
    echo "=== Prova bring-up manuale sulla prima interfaccia USB ==="
    local target=""
    while read -r iface _rest; do
        [ -z "$iface" ] && continue
        [[ "$iface" =~ $EXCLUDE_RE ]] && continue
        target="$iface"; break
    done < <(ip -br link 2>/dev/null)
    if [ -z "$target" ]; then
        echo "  NESSUNA interfaccia USB trovata."
    else
        echo "  Interfaccia target: $target"
        echo "  --- nmcli con add + up ---"
        nmcli con add type ethernet ifname "$target" con-name "usb-tether-diag" \
            ipv4.method auto ipv6.method ignore \
            connection.autoconnect no ipv4.never-default yes 2>&1 | sed 's/^/    /'
        echo "  --- nmcli con up (timeout 30s) ---"
        timeout 30 nmcli con up "usb-tether-diag" 2>&1 | sed 's/^/    /'
        echo "  --- IPv4 ottenuto? ---"
        if ip -4 addr show dev "$target" 2>/dev/null | grep -q 'inet '; then
            ip -4 addr show dev "$target" 2>/dev/null | grep 'inet ' | sed 's/^/    /'
            ip route show dev "$target" 2>/dev/null | sed 's/^/    /'
        else
            echo "    NESSUN IPv4: NM non e' riuscito a fare DHCP."
        fi
        echo "  --- cleanup ---"
        nmcli con delete "usb-tether-diag" 2>&1 | sed 's/^/    /'
    fi
}

# --- main -------------------------------------------------------------------
case "${1:-status}" in
    detect)   cmd_detect ;;
    activate) shift; cmd_activate "$@" ;;
    restore)  cmd_restore ;;
    status)   cmd_status ;;
    diagnose) cmd_diagnose ;;
    _watch)   shift; cmd_watch "$@" ;;
    *)
        echo "Uso: $0 {detect|activate [max_min] [intranet|server]|restore|status|diagnose}" >&2
        exit 64
        ;;
esac
