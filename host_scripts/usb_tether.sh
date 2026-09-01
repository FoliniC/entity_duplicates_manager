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
#   usb_tether.sh _drain <table> <mark> [max_wait] -> interno: drenaggio grace
#
# Prerequisiti per la protezione stream lato router (Echo/Alexa ecc.):
#   - apt install conntrack (su Debian, per il drenaggio locale)
#   - installare tethering-graceful.sh su OpenWrt (vedi script separato)
#   - impostare PROTECTED_DEVICE_IP qui sotto con l'IP riservato del device
# ============================================================================

set -u

# --- Costanti ---
STATE_FILE="/run/usb_tether_state"
PID_FILE="/run/usb_tether_watcher.pid"
LAN_NET="192.168.0.0/24"
LAN_IF="enp2s0"                       # interfaccia LAN del server
ROUTER_IP="192.168.0.11"              # IP router OpenWrt (sorgente traffico da NATare)
ROUTER_SSH_KEY="/home/carlo/docker/homeassistant/config/.ssh/router_key"
ROUTER_ROUTE_METRIC=9                 # metric della route intranet sul router.
                                      # VALE 9 = INFERIORE a usb0 (metric 10) cosi' l'anchor
                                      # intranet vince SEMPRE sulla WAN locale anche quando netifd
                                      # re-inietta la rotta usb0 metric 10 (bug "Intranet morta").
                                      # Restore/renat usano la stessa metrica, quindi sono idempotenti.
ROUTER_WAN_IF="usb0"                  # interfaccia WAN USB del router OpenWrt

# --- Graceful transition: tabelle/mark dedicati per non collidere fra loro ---
LOCAL_TABLE_ACTIVATE=81      # Debian: swap verso il telefono (mark 0x1, esistente)
LOCAL_TABLE_RESTORE=82       # Debian: swap dal telefono alla LAN (mark 0x2, esistente)
LOCAL_DRAIN_CEILING=1800     # 30 min - protegge TUTTE le connessioni stabilite, non solo una
ROUTER_TABLE_LEAVE_WAN=88    # Router: lascia la propria WAN/tethering locale
ROUTER_MARK_LEAVE_WAN=0x88
ROUTER_TABLE_LEAVE_ANCHOR=89 # Router: lascia il fallback via Debian/Windows
ROUTER_MARK_LEAVE_ANCHOR=0x89
ROUTER_DRAIN_CEILING=21600   # 6h - scoped a un solo device, tetto piu' permissivo
ROUTER_GRACEFUL_SCRIPT="/usr/bin/tethering-graceful.sh"
# IP riservato (DHCP statico) del device da proteggere in modo prioritario
# sul router, es. Echo. Vuoto = router_graceful_* diventano no-op sicuri.
PROTECTED_DEVICE_IP="192.168.0.90"        # <-- IMPOSTARE (es. "192.168.0.50")
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
# Robusto: retry con backoff + verifica che la route sia effettivamente presente.
router_add_fallback_route() {
    local max_retries=3
    local retry=0
    local target_gw="192.168.0.3"
    local target_dev="br-lan"
    local target_metric="$ROUTER_ROUTE_METRIC"
    local route_cmd="ip route replace default via $target_gw dev $target_dev metric $target_metric"
    local verify_cmd="ip route show default | grep -q \"via $target_gw dev $target_dev metric $target_metric\""

    # Se la route e' gia' presente, nessun bisogno di aggiungerla (evita errori
    # su "replace" quando la route e' identica o il router la ha gia' ripristinata).
    if router_ssh "$verify_cmd"; then
        echo "Route fallback gia' presente sul router (metric $target_metric) - nessuna azione necessaria."
        return 0
    fi

    while [ $retry -lt $max_retries ]; do
        if router_ssh "$route_cmd"; then
            sleep 1  # dai tempo al kernel di aggiornare la tabella
            if router_ssh "$verify_cmd"; then
                echo "Route fallback aggiunta sul router (metric $target_metric) - verificata."
                return 0
            else
                echo "WARN: route command succeeded but verification failed (retry $((retry+1))/$max_retries)" >&2
            fi
        else
            echo "WARN: router_ssh failed for route add (retry $((retry+1))/$max_retries)" >&2
        fi
        retry=$((retry + 1))
        [ $retry -lt $max_retries ] && sleep $((retry * 2))  # backoff: 2s, 4s
    done

    echo "ERRORE: impossibile aggiungere route fallback sul router dopo $max_retries tentativi." >&2
    return 1
}

router_del_fallback_route() {
    # Protegge (se PROTECTED_DEVICE_IP e' configurato) i flussi del device
    # che stavano ancora usando l'anchor prima di toglierla.
    router_graceful_begin "$ROUTER_TABLE_LEAVE_ANCHOR" "$ROUTER_MARK_LEAVE_ANCHOR" "192.168.0.3" "br-lan"
    
    local max_retries=3
    local retry=0
    local target_gw="192.168.0.3"
    local target_dev="br-lan"
    local target_metric="$ROUTER_ROUTE_METRIC"
    local route_cmd="ip route del default via $target_gw dev $target_dev metric $target_metric 2>/dev/null; true"
    local verify_cmd="! ip route show default | grep -q \"via $target_gw dev $target_dev metric $target_metric\""
    
    while [ $retry -lt $max_retries ]; do
        if router_ssh "$route_cmd"; then
            sleep 1
            if router_ssh "$verify_cmd"; then
                echo "Route fallback rimossa dal router - verificata."
                router_graceful_end "$ROUTER_TABLE_LEAVE_ANCHOR" "$ROUTER_MARK_LEAVE_ANCHOR" "$ROUTER_DRAIN_CEILING"
                return 0
            else
                echo "WARN: route del command succeeded but route still present (retry $((retry+1))/$max_retries)" >&2
            fi
        else
            echo "WARN: router_ssh failed for route del (retry $((retry+1))/$max_retries)" >&2
        fi
        retry=$((retry + 1))
        [ $retry -lt $max_retries ] && sleep $((retry * 2))
    done
    
    echo "ERRORE: impossibile rimuovere route fallback dal router dopo $max_retries tentativi." >&2
    router_graceful_end "$ROUTER_TABLE_LEAVE_ANCHOR" "$ROUTER_MARK_LEAVE_ANCHOR" "$ROUTER_DRAIN_CEILING"
    return 1
}

# Legge da netifd il gateway DHCP attuale della WAN USB del router.
router_wan_gateway() {
    router_ssh "ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1" \
        | tr -d '\r'
}

# Legge il gateway ATTUALMENTE in uso sulla route WAN attiva (non lo stato
# DHCP di netifd, la route vera - e' quella che va preservata in transizione).
router_current_wan_gw() {
    router_ssh "ip route show default dev $ROUTER_WAN_IF metric 10 2>/dev/null | awk '{print \$3; exit}'" \
        | tr -d '\r'
}

# Toglie/ripristina la WAN primaria del router per forzare tutto il traffico via server.
router_wan_down() {
    local cur_gw
    cur_gw=$(router_current_wan_gw)
    if [[ "$cur_gw" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        router_graceful_begin "$ROUTER_TABLE_LEAVE_WAN" "$ROUTER_MARK_LEAVE_WAN" "$cur_gw" "$ROUTER_WAN_IF"
    fi
    # Disattiva l'interfaccia WAN su netifd: rimuove la route e impedisce a
    # netifd di ri-aggiungerla (altrimenti il ciclo "ip route del" rimuove solo
    # la route corrente ma netifd la reinserisce entro secondi, riportando la
    # LAN su un upstream morto).
    router_ssh "ifdown wan >/dev/null 2>&1; true" \
        && echo "WAN router disattivata (ifdown wan)." \
        || echo "WARN: ifdown wan fallito." >&2
    # BLOCCO PRESERVATIVO: l'hotplug USB del telefono router o un evento di
    # carrier sul router OpenWrt (netifd) ri-aggiungono la rotta usb0 metric 10
    # ENTRO SECONDI, anche se l'interfaccia e' "down". Questo riporterebbe la LAN
    # su un upstream morto e riprodurrebbe il bug "Intranet morta".
    # Impostiamo auto=0: netifd non riporta up l'interfaccia wan in autonomia
    # (blocca la re-iniezione usb0 metric 10), ma lascia intatto il proto cosi'
    # che il restore (router_wan_up -> ifup wan) funzioni ancora. Idempotente.
    router_ssh "uci set network.wan.auto='0'; uci commit network; true" \
        && echo "WAN router bloccata (auto=0) per evitare re-iniezione usb0." \
        || echo "WARN: blocco uci wan fallito (riprovare a mano: uci set network.wan.auto=0; uci commit)." >&2
    if [[ "$cur_gw" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        router_graceful_end "$ROUTER_TABLE_LEAVE_WAN" "$ROUTER_MARK_LEAVE_WAN" "$ROUTER_DRAIN_CEILING"
    fi
}

router_wan_up() {
    local gw
    # Ripristina auto=1 (eventualmente impostato da router_wan_down per bloccare
    # la re-iniezione usb0 metric 10 in intranet). Con auto=1 il successivo
    # ifup wan riporta su la WAN reale senza problemi.
    router_ssh "uci set network.wan.auto='1'; uci commit network; true" >/dev/null 2>&1 || true
    # router_ssh ha gia' ConnectTimeout=5: se il router non risponde, fallisce
    # velocemente. Il vecchio ramo ADB (airplane-mode toggle) che si bloccava
    # per minuti e' stato rimosso. Se la WAN non si attiva, ripristiniamo il
    # fallback Debian invece di isolare la LAN.
    router_ssh "/usr/bin/adb_router shell settings put global airplane_mode 0 >/dev/null 2>&1; /usr/bin/adb_router shell settings put global mobile_data 1 >/dev/null 2>&1; /usr/bin/adb_router shell svc data enable >/dev/null 2>&1; /usr/bin/adb_router shell settings put global tether_upstream_types 0,5 >/dev/null 2>&1; /usr/bin/adb_router shell settings put global mobile_data_always_on 1 >/dev/null 2>&1; /usr/bin/adb_router shell settings put global network_avoid_bad_wifi 1 >/dev/null 2>&1; /usr/bin/adb_router shell settings put global wifi_calling_enabled 0 >/dev/null 2>&1; /usr/bin/adb_router shell svc usb setFunctions rndis >/dev/null 2>&1; /usr/bin/enable_usb_tether.sh >/dev/null 2>&1; ifup wan >/dev/null 2>&1"
    # Se usb0 non si e' creata (telefono in standby / tethering non partito),
    # forza il tethering RNDIS via service call connectivity e riprova.
    if ! router_ssh "ip link show $ROUTER_WAN_IF >/dev/null 2>&1"; then
        router_ssh "/usr/bin/adb_router shell service call connectivity 33 i32 1 >/dev/null 2>&1; sleep 4; /usr/bin/adb_router shell svc usb setFunctions rndis >/dev/null 2>&1; ifup wan >/dev/null 2>&1" >/dev/null 2>&1 || true
        sleep 3
    fi
    sleep 3
    gw=$(router_wan_gateway | head -1)
    if [[ "$gw" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        router_ssh "ip route replace default via $gw dev $ROUTER_WAN_IF metric 10 2>/dev/null; true"
        echo "WAN router riattivata (route $ROUTER_WAN_IF via $gw ripristinata)."
    fi

    # VERIFICA CONNETTIVITA' INTERNET REALE DEL ROUTER
    if router_ssh "ping -c 2 -W 3 1.1.1.1 >/dev/null 2>&1 || ping -c 2 -W 3 8.8.8.8 >/dev/null 2>&1"; then
        echo "OK: router WAN connettivita' internet verificata."
        return 0
    fi

    # WAN non raggiungibile (es. telefono non sul router in modalita' intranet).
    # NON lasciare il router isolato: se la WAN non funziona, ripristina il
    # fallback su Debian perche' la LAN continui ad avere Internet.
    echo "WARN: router WAN privo di internet - ripristino fallback su Debian per evitare isolamento LAN." >&2
    router_add_fallback_route || echo "ERROR: impossibile ripristinare fallback Debian!" >&2
    return 1
}

# ============================================================================
# --- Graceful transition -----------------------------------------------------
# Protegge le connessioni ESTABLISHED/RELATED durante uno swap di default
# route, finche' non terminano davvero (o scade un tetto di sicurezza),
# mentre le connessioni NUOVE usano subito il nuovo percorso.
#
# Due bug classici da evitare (entrambi presenti nella versione precedente):
#  1. "ip rule fwmark X lookup main" non ha ALCUN effetto se 'main' ha piu'
#     default route a metriche diverse: la scelta della rotta in una tabella
#     dipende solo dalla metrica, mai dal mark. Serve una tabella dedicata.
#  2. "CONNMARK --set-mark" da solo marca SOLO la connessione in conntrack,
#     mai il pacchetto: senza un "CONNMARK --restore-mark" a monte, "ip rule
#     fwmark" non scatta MAI (il meccanismo diventa un no-op silenzioso).
#
# Inoltre la tabella dedicata deve contenere anche la subnet LAN come route
# on-link: altrimenti anche il traffico di ritorno verso host LAN (marcato,
# perche' appartiene alla stessa connessione) cadrebbe sulla route di
# default della tabella e uscirebbe dall'interfaccia sbagliata.
# ============================================================================

graceful_begin() {
    local table_id="$1" mark="$2" old_gw="$3" old_dev="$4" snapshot_seconds="${5:-5}"
    local chain="TETHER_LOCAL_${mark}"

    iptables -t mangle -N "$chain" 2>/dev/null || true
    iptables -t mangle -C PREROUTING -j "$chain" 2>/dev/null \
        || iptables -t mangle -A PREROUTING -j "$chain"
    iptables -t mangle -F "$chain"
    iptables -t mangle -A "$chain" -j CONNMARK --restore-mark

    ip route add "$LAN_NET" dev "$LAN_IF" table "$table_id" 2>/dev/null || true
    ip route replace default via "$old_gw" dev "$old_dev" table "$table_id"
    ip rule del fwmark "$mark" lookup "$table_id" 2>/dev/null || true
    ip rule add fwmark "$mark" lookup "$table_id" pref 100

    # SNAPSHOT breve, poi rimuove la regola di marcatura (resta solo
    # restore-mark): se restasse attiva per tutto il drenaggio, marcherebbe
    # via via anche connessioni NUOVE che diventano ESTABLISHED nel
    # frattempo, dirottandole per errore sul vecchio percorso.
    iptables -t mangle -A "$chain" -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-mark "$mark"
    sleep "$snapshot_seconds"
    iptables -t mangle -D "$chain" -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-mark "$mark"
}

# Avvia il drenaggio in background (stesso pattern di auto-invocazione del
# watchdog: setsid + self-exec) cosi' la chiamata ritorna subito anche se
# il tetto di sicurezza e' di ore, non secondi.
graceful_end_async() {
    local table_id="$1" mark="$2" max_wait="${3:-1800}"
    setsid bash "$0" _drain "$table_id" "$mark" "$max_wait" >/dev/null 2>&1 < /dev/null &
}

# --- SSH al router: stesso meccanismo begin/end, ma sul lato OpenWrt --------
# Richiede /usr/bin/tethering-graceful.sh installato sul router (vedi script
# separato). Se PROTECTED_DEVICE_IP e' vuota, non fa nulla (no-op sicuro).
router_graceful_begin() {
    local table_id="$1" mark="$2" old_gw="$3" old_dev="$4"
    [ -z "$PROTECTED_DEVICE_IP" ] && return 0
    router_ssh "$ROUTER_GRACEFUL_SCRIPT begin $table_id $mark $PROTECTED_DEVICE_IP $old_gw $old_dev" \
        && echo "Router: protezione flussi attiva per $PROTECTED_DEVICE_IP (table $table_id)." \
        || echo "WARN: router_graceful_begin fallito (script installato sul router?)." >&2
}

router_graceful_end() {
    local table_id="$1" mark="$2" max_wait="${3:-21600}"
    [ -z "$PROTECTED_DEVICE_IP" ] && return 0
    router_ssh "$ROUTER_GRACEFUL_SCRIPT end $table_id $mark $max_wait" \
        && echo "Router: drenaggio avviato (table $table_id, tetto ${max_wait}s)." \
        || echo "WARN: router_graceful_end fallito." >&2
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
    iptables -t nat -C POSTROUTING -s "$LAN_NET" -o "$phone_if" \
        -m comment --comment "usb_tether_router_nat" -j MASQUERADE 2>/dev/null \
        || iptables -t nat -A POSTROUTING -s "$LAN_NET" -o "$phone_if" \
            -m comment --comment "usb_tether_router_nat" -j MASQUERADE
    # 3) Forwarding: usa -I (insert in testa) invece di -A (append) per avere
    #    priorita' sulle regole DROP di Docker che si trovano in coda alla chain.
    iptables -C FORWARD -s "$LAN_NET" -o "$phone_if" \
        -m comment --comment "usb_tether_router_fwd" -j ACCEPT 2>/dev/null \
        || iptables -I FORWARD 1 -s "$LAN_NET" -o "$phone_if" \
            -m comment --comment "usb_tether_router_fwd" -j ACCEPT
    iptables -C FORWARD -d "$LAN_NET" -i "$phone_if" \
        -m comment --comment "usb_tether_router_fwd" -j ACCEPT 2>/dev/null \
        || iptables -I FORWARD 1 -d "$LAN_NET" -i "$phone_if" \
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

    # Porta UP a livello link prima di NM (necessario per RNDIS/USB
    # tethering che altrimenti resta DOWN anche se NM ha la connessione).
    ip link set "$iface" up 2>/dev/null || true
    sleep 1

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
    # Rimuovi solo la default route via telefono se presente (metric 50)
    ip route del default metric 50 dev "$iface" 2>/dev/null || true
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

                # Carico fisico Ethernet ha carrier. Interfacce USB RNDIS/CDC-ether
        # (tethering telefono) non hanno carrier sysfs: le accettiamo se
        # il dispositivo USB e' presente (indicato dalla presenza dell'interfaccia
        # con tipo ARPHRD_ETHER ma nome non fisico).
        if [ -r "/sys/class/net/$iface/carrier" ]; then
            carrier=$(cat "/sys/class/net/$iface/carrier" 2>/dev/null)
            [ "$carrier" = "1" ] || continue
        else
            true
        fi

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
        # NOTA: "ip route get" verifica solo la raggiungibilita', non esclude
        # la LAN da solo -> serve il controllo esplicito sul prefisso.
        if [[ "$gw" != 192.168.0.* ]] && ip route get "$gw" >/dev/null 2>&1; then
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

    # Gia' attivo? In modalita' intranet NON rifiutiamo: il bottone 🌐 Intranet
    # deve essere CORRETTIVO/idempotente (es. la WAN router usb0 e' rimasta
    # primaria e morta, o la metrica dell'anchor e' sbagliata). In quel caso
    # riapplichiamo il routing intranet senza forzare un restore+activate.
    # Nelle altre modalita' (server/normale) il blocco resta per evitare doppi swap.
    if [ -f "$STATE_FILE" ]; then
        local cur_state
        cur_state=$(grep -E '^state=' "$STATE_FILE" 2>/dev/null | cut -d= -f2-)
        if [ "$cur_state" = "active" ]; then
            if [ "$mode" = "intranet" ]; then
                echo "INTRANET gia' segnata attiva: riapplico routing correttivo (WAN router down + anchor metric $ROUTER_ROUTE_METRIC + NAT)." >&2
                router_wan_down
                # Garantisce (idempotente) che l'anchor verso l'host sia presente
                # a metric $ROUTER_ROUTE_METRIC (9), cosi' vince su usb0 metric 10
                # anche se netifd la re-inietta.
                router_add_fallback_route || echo "WARN: ripristino anchor intranet fallito." >&2
                # Rileva l'interfaccia USB corrente (quella che porta a Internet su
                # Debian) e riapplica MASQUERADE+FORWARD: senza di questo la LAN
                # non naviga e il failsafe cancella il passaggio.
                local phone_if
                phone_if=$(ip route get 8.8.8.8 2>/dev/null | awk '{for(i=1;i<=NF;i++){if($i=="dev"){print $(i+1); exit}}}')
                [ -z "$phone_if" ] && phone_if=$(ip -br addr show 2>/dev/null | grep -E '^enx' | awk '{print $1}' | head -1)
                if [ -n "$phone_if" ]; then
                    enable_nat_router "$phone_if" || echo "WARN: riapplicazione NAT intranet fallita." >&2
                else
                    echo "WARN: interfaccia telefono non rilevata, NAT non riapplicato." >&2
                fi
                # Aggiorna il STATE_FILE con l'interfaccia corrente (altrimenti
                # cmd_status legge la vecchia phone_if morta e ritorna 'error',
                # facendo scattare il failsafe). Rileva gw e lan_gw attuali.
                local cur_gw cur_lan_gw now_ts exp_ts
                cur_gw=$(ip route get 8.8.8.8 2>/dev/null | awk '{for(i=1;i<=NF;i++){if($i=="via"){print $(i+1); exit}}}')
                [ -z "$cur_gw" ] && cur_gw="$gw"
                cur_lan_gw=$(get_default_gw); [ -z "$cur_lan_gw" ] && cur_lan_gw="192.168.0.11"
                now_ts=$(now_epoch); exp_ts=$((now_ts + max_min * 60))
                {
                    echo "state=active"
                    echo "mode=$mode"
                    echo "phone_if=$phone_if"
                    echo "phone_gw=$cur_gw"
                    echo "lan_gw=$cur_lan_gw"
                    echo "activated_at=$now_ts"
                    echo "expire_at=$exp_ts"
                } > "$STATE_FILE"
                echo "Modalita' INTRANET (correttiva): WAN router down, anchor + NAT + stato ripristinati."
                return 0
            else
                echo "GIA ATTIVO: usa 'restore' prima di riattivare." >&2
                return 1
            fi
        fi
    fi

    # Rileva il telefono.
    local det iface gw
    det=$(cmd_detect) || true
    
    # Se cmd_detect non trova nulla, prova a cercare l'interfaccia RNDIS Xiaomi
    # (VID 2717) dinamicamente come fallback.
    if [ -z "$det" ]; then
        local rndis_iface=""
        while read -r iface_name _rest; do
            [ -z "$iface_name" ] && continue
            if udevadm info "/sys/class/net/$iface_name" 2>/dev/null | grep -q "ID_VENDOR_ID=2717"; then
                rndis_iface="$iface_name"
                break
            fi
        done < <(ip -br link 2>/dev/null | grep -E '^enx|^rndis|^usb')
        
        if [ -n "$rndis_iface" ]; then
            # Porta UP l'interfaccia e ottieni IP
            ip link set "$rndis_iface" up 2>/dev/null || true
            sleep 1
            
            local conn_name="usb-tether-${rndis_iface}"
            nmcli con delete "$conn_name" >/dev/null 2>&1 || true
            nmcli con add type ethernet ifname "$rndis_iface" con-name "$conn_name" \
                ipv4.method auto ipv6.method ignore \
                connection.autoconnect no \
                ipv4.never-default yes >/dev/null 2>&1 || true
            timeout 15 nmcli con up "$conn_name" >/dev/null 2>&1 || true
            sleep 1
            
            # Trova il gateway
            gw=$(ip route | grep "dev $rndis_iface" | grep -oE 'via [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | awk '{print $2}' | head -1)
            if [ -z "$gw" ]; then
                gw="172.21.40.55"
            fi
            
            # Verifica IPv4
            ip -4 addr show dev "$rndis_iface" 2>/dev/null | grep -q 'inet ' || {
                echo "ERRORE: $rndis_iface non ha IP dopo DHCP" >&2
                nmcli con delete "$conn_name" >/dev/null 2>&1 || true
                return 2
            }
            
            iface="$rndis_iface"
            det="${iface}|${gw}"
        fi
    fi
    
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

    # Aggiungi la default route via telefono con metrica PIU BASSA (vince per NUOVE connessioni).
    # Manteniamo la route LAN esistente (metric 100) per far defluire le connessioni gia' aperte.
    if ! ip route add default via "$gw" dev "$iface" metric 50 2>/dev/null; then
        ip route replace default via "$gw" dev "$iface" metric 50 2>/dev/null || {
            echo "Impossibile aggiungere la route via $iface." >&2
            return 3
        }
    fi

    # Abilita NAT/forwarding per traffico router -> telefono.
    enable_nat_router "$iface"

    # GRACEFUL TRANSITION (locale): protegge le connessioni ESTABLISHED del
    # server finche' non finiscono davvero (o scade il tetto), poi ripulisce.
    # "Vecchio" percorso = LAN/router (quello in uso prima di questa activate).
    if command -v iptables >/dev/null 2>&1; then
        graceful_begin "$LOCAL_TABLE_ACTIVATE" 0x1 "$lan_gw" "$LAN_IF"
        graceful_end_async "$LOCAL_TABLE_ACTIVATE" 0x1 "$LOCAL_DRAIN_CEILING"
    fi

    # Se modalita' intranet, disabilita SUBITO la WAN router: il router ha
    # una propria protezione indipendente (router_graceful_*, dentro
    # router_wan_down) per il device configurato in PROTECTED_DEVICE_IP -
    # non serve piu' aspettare il drenaggio locale del server per farlo.
    local intranet_mode="false"
    if [ "$mode" = "intranet" ]; then
        intranet_mode="true"
        router_wan_down
        echo "Modalita' INTRANET: WAN router disattivata (protezione flussi lato router attiva)."
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

# --- rndis_activate -------------------------------------------------------
# Attivazione tethering USB Xiaomi RNDIS bypassando cmd_detect.
# Usa quando l'interfaccia RNDIS Xiaomi esiste ma cmd_detect non la rileva
# perche' non ha carrier sysfs. L'interfaccia viene identificata dinamicamente
# cercando un dispositivo USB Xiaomi (VID 2717) con interfaccia RNDIS.
cmd_rndis_activate() {
    local max_min="${1:-30}" mode="${2:-server}"
    local max_min_valid="${max_min:-30}" mode_valid="$mode"
    case "$max_min_valid" in
        ''|*[!0-9]*) max_min_valid=30 ;;
    esac
    [ "$max_min_valid" -lt 1 ] 2>/dev/null && max_min_valid=1
    [ "$max_min_valid" -gt 480 ] 2>/dev/null && max_min_valid=480

    # Trova dinamicamente l'interfaccia RNDIS Xiaomi (VID 2717).
    local iface=""
    while read -r iface_name _rest; do
        [ -z "$iface_name" ] && continue
        # Verifica se e' un'interfaccia USB Xiaomi via ethtool/devpath
        if udevadm info "/sys/class/net/$iface_name" 2>/dev/null | grep -q "ID_VENDOR_ID=2717"; then
            iface="$iface_name"
            break
        fi
    done < <(ip -br link 2>/dev/null | grep -E '^enx|^rndis|^usb')

    # Fallback: cerca per nome che inizia con enx (MAC-based)
    if [ -z "$iface" ]; then
        iface=$(ip -br link 2>/dev/null | grep -E '^enx' | awk '{print $1}' | head -1)
    fi

    if [ -z "$iface" ]; then
        echo "ERRORE: Nessuna interfaccia RNDIS Xiaomi trovata" >&2
        return 2
    fi

    echo "Interfaccia RNDIS rilevata: $iface" >&2

    # Porta UP l'interfaccia
    ip link set "$iface" up 2>/dev/null || true
    sleep 0.5

    # Assegna IP via NM DHCP (timeout ridotto).
    local conn_name="usb-tether-${iface}"
    nmcli con delete "$conn_name" >/dev/null 2>&1 || true
    nmcli con add type ethernet ifname "$iface" con-name "$conn_name" \
        ipv4.method auto ipv6.method ignore \
        connection.autoconnect no \
        ipv4.never-default yes >/dev/null 2>&1 || true
    timeout 15 nmcli con up "$conn_name" >/dev/null 2>&1 || true
    sleep 1

    # Trova il gateway del telefono.
    local gw
    gw=$(ip route | grep "dev $iface" | grep -oE 'via [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | awk '{print $2}' | head -1)
    if [ -z "$gw" ]; then
        gw="172.21.40.55"
    fi

    # Verifica che l'interfaccia abbia un IPv4.
    ip -4 addr show dev "$iface" 2>/dev/null | grep -q 'inet ' || {
        echo "ERRORE: $iface non ha IP dopo DHCP" >&2
        nmcli con delete "$conn_name" >/dev/null 2>&1 || true
        return 2
    }

    local lan_gw
    lan_gw=$(get_default_gw)
    [ -z "$lan_gw" ] && lan_gw="192.168.0.11"

    # Aggiungi default route via telefono con metrica PIU BASSA.
    ip route add default via "$gw" dev "$iface" metric 50 2>/dev/null \
        || ip route replace default via "$gw" dev "$iface" metric 50 2>/dev/null || {
        echo "Impossibile aggiungere la route via $iface." >&2
        return 3
    }

    enable_nat_router "$iface"

    # GRACEFUL TRANSITION (locale): vedi cmd_activate per i dettagli del perche'
    # serve una tabella dedicata + restore-mark invece del vecchio "lookup main".
    if command -v iptables >/dev/null 2>&1; then
        graceful_begin "$LOCAL_TABLE_ACTIVATE" 0x1 "$lan_gw" "$LAN_IF"
        graceful_end_async "$LOCAL_TABLE_ACTIVATE" 0x1 "$LOCAL_DRAIN_CEILING"
    fi

    if [ "$mode_valid" = "intranet" ]; then
        router_wan_down
        echo "Modalita' INTRANET: WAN router disattivata (protezione flussi lato router attiva)."
    fi

    local now expire
    now=$(now_epoch)
    expire=$((now + max_min_valid * 60))

    {
        echo "state=active"
        echo "mode=$mode_valid"
        echo "phone_if=$iface"
        echo "phone_gw=$gw"
        echo "lan_gw=$lan_gw"
        echo "activated_at=$now"
        echo "expire_at=$expire"
    } > "$STATE_FILE"

    if [ -f "$PID_FILE" ]; then
        kill "$(cat "$PID_FILE" 2>/dev/null)" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
    setsid bash "$0" _watch "$expire" >/dev/null 2>&1 < /dev/null &
    echo $! > "$PID_FILE"

    echo "OK attivato: $iface via $gw per ${max_min_valid} min (modalita $mode_valid)."
    return 0
}

# --- restore ----------------------------------------------------------------
# Idempotente: rimuove la route del telefono, killa il watcher, cancella stato.
# GRACEFUL: mantiene la route tethering per 30s per far defluire le connessioni
# attive, marcandole per continuare via tethering mentre le nuove usano WAN.
cmd_restore() {
    local phone_if="" phone_gw=""

    # Killa sempre il watcher se presente.
    if [ -f "$PID_FILE" ]; then
        local wpid
        wpid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$wpid" ]; then
            kill -- "-$wpid" 2>/dev/null || kill "$wpid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi

    # Rimuovi la route del telefono se presente nello stato o a runtime.
    if [ -f "$STATE_FILE" ]; then
        phone_if=$(grep -E '^phone_if=' "$STATE_FILE" | cut -d= -f2-)
        phone_gw=$(grep -E '^phone_gw=' "$STATE_FILE" | cut -d= -f2-)
    fi

    # Protegge SUBITO (prima di router_wan_up) i flussi che sul router stanno
    # ancora usando l'anchor. Se aspettassimo che lo faccia
    # router_del_fallback_route (chiamata molto piu' avanti, dentro
    # disable_nat_router), ci sarebbe una finestra in cui router_wan_up ha
    # gia' fatto preferire la WAN locale nella tabella 'main' del router, ma
    # nessuno protegge ancora i flussi vecchi sull'anchor: verrebbero
    # silenziosamente dirottati prima che la marcatura sia pronta. E' un
    # no-op sicuro se PROTECTED_DEVICE_IP non e' configurato, e idempotente
    # se router_del_fallback_route la richiama poco dopo.
    router_graceful_begin "$ROUTER_TABLE_LEAVE_ANCHOR" "$ROUTER_MARK_LEAVE_ANCHOR" "192.168.0.3" "br-lan"

    # GRACEFUL RESTORE: se c'era una route tethering, protegge le connessioni
    # ESTABLISHED finche' non finiscono davvero (o scade il tetto), invece di
    # un timer fisso - una radio in streaming non "finisce" mai da sola entro
    # nessun timer ragionevole, quindi un timer fisso la interrompe comunque.
    if [ -n "$phone_if" ] && [ -n "$phone_gw" ] && ip route show | grep -q "default via $phone_gw dev $phone_if metric 50"; then
        echo "Restore graceful: protezione connessioni tethering avviata..." >&2

        # 1. Protegge le connessioni ESTABLISHED via telefono in una tabella
        #    dedicata PRIMA di toccare la route in main (altrimenti per un
        #    istante nessuno le protegge).
        graceful_begin "$LOCAL_TABLE_RESTORE" 0x2 "$phone_gw" "$phone_if"

        # 2. Ripristina la WAN del router (route del router, indipendente).
        # In Intranet il telefono e' su Debian, quindi la WAN del router NON ha
        # internet per definizione: router_wan_up rileva il ping fallito e
        # ripristina il fallback Debian, ma NON deve far abortire il restore.
        # Il passaggio a "Normale" deve completare comunque (rimuove anchor
        # Intranet + stato), anche se la WAN sara' isolata finche' non torna
        # attiva (es. telefono ricollegato al router / modem).
        router_wan_up || echo "WARN: WAN router riattivata ma senza internet verificato; la LAN sara' isolata finche' la WAN non sara' attiva. Proseguo con la pulizia dello stato." >&2

        # 3. Rimuovi SUBITO la route telefono da main: le nuove connessioni
        #    vedono solo la LAN/router come default. Quelle marcate restano
        #    protette dalla tabella dedicata (ip rule fwmark 0x2).
        ip route del default via "$phone_gw" dev "$phone_if" metric 50 2>/dev/null || true
        while ip route del default metric 50 2>/dev/null; do :; done

        # 4. Drena in background finche' i flussi marcati non finiscono
        #    davvero (o scade il tetto), poi ripulisce tabella/rule/chain.
        graceful_end_async "$LOCAL_TABLE_RESTORE" 0x2 "$LOCAL_DRAIN_CEILING"
    else
        # Nessuna route tethering gestita da STATE_FILE.
        # Ma nella NORMALE il tethering del Note 13 Pro 5G (via DHCP su enx*)
        # potrebbe aver sovrascritto la default route via router (192.168.0.11):
        # in questo caso il router NON fornisce Internet, perche' Debian esce
        # direttamente via telefono invece del router. Rileva e correggi.
        router_wan_up || echo "WARN: WAN router riattivata ma senza internet verificato. Proseguo con la pulizia dello stato." >&2
        # Se la default route punta a un IP NOT-VIA-192.168.0.11 (es. 10.87.160.73),
        # togli la route del telefono cosi' la rete LAN usa il router (NORMALE).
        local cur_gw
        cur_gw=$(get_default_gw)
        if [ -n "$cur_gw" ] && [ "$cur_gw" != "192.168.0.11" ]; then
            echo "Restore NORMALE: rimuovo route del telefono ($cur_gw) -> uso router 192.168.0.11" >&2
            while ip route del default metric 50 2>/dev/null; do :; done
            ip route del default 2>/dev/null || true
            ip route add default via 192.168.0.11 dev "$LAN_IF" metric 101 2>/dev/null || true
        fi
    fi

    # Pulizia finale idempotente (no-op se il ramo sopra ha gia' rimosso tutto).
    while ip route del default metric 50 2>/dev/null; do :; done

    # Rimuovi la connessione NM temporanea creata da bring_up_iface, se presente.
    if [ -n "$phone_if" ]; then
        tear_down_iface "$phone_if"
    fi

    # Disabilita NAT/forwarding per traffico router.
    disable_nat_router "$phone_if"

    # Pulizia extra: se un drenaggio dell'ultima activate fosse ancora appeso,
    # chiudilo subito - stiamo comunque tornando definitivamente alla LAN.
    iptables -t mangle -F "TETHER_LOCAL_0x1" 2>/dev/null || true
    ip rule del fwmark 0x1 lookup "$LOCAL_TABLE_ACTIVATE" 2>/dev/null || true
    ip route flush table "$LOCAL_TABLE_ACTIVATE" 2>/dev/null || true

    rm -f "$STATE_FILE"
    echo "OK ripristinato: default route tornata alla LAN (graceful)."
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

# --- _drain (interno) --------------------------------------------------------
# Aspetta che non ci siano piu' connessioni con quel mark (o scada il tetto),
# poi ripulisce chain/rule/tabella. Lanciato via graceful_end_async (self-exec
# con setsid, stesso pattern del watchdog: sopravvive a fine sessione SSH).
cmd_drain() {
    local table_id="$1" mark="$2" max_wait="${3:-1800}"
    local chain="TETHER_LOCAL_${mark}"
    local waited=0 count=1

    if ! command -v conntrack >/dev/null 2>&1; then
        # Senza conntrack-tools non sappiamo quando i flussi finiscono davvero:
        # fallback al vecchio comportamento (tempo fisso). Consigliato:
        # apt install conntrack
        sleep "$max_wait"
    else
        while [ "$waited" -lt "$max_wait" ]; do
            count=$(conntrack -L -m "$((mark))" 2>/dev/null | grep -Ec '^(tcp|udp|icmp|unknown|sctp)')
            [ "${count:-0}" -eq 0 ] && break
            sleep 20
            waited=$((waited + 20))
        done
    fi

    iptables -t mangle -F "$chain" 2>/dev/null || true
    ip rule del fwmark "$mark" lookup "$table_id" 2>/dev/null || true
    ip route flush table "$table_id" 2>/dev/null || true
    logger -t usb_tether "drain table $table_id (mark $mark) completato dopo ${waited}s" 2>/dev/null || true
}

# --- status -----------------------------------------------------------------
# Stampa JSON con stato + attributi. E' la fonte di verita' per HA.
cmd_status() {
    local state="idle" mode="server" phone_if="" phone_gw="" lan_gw="" active_since="" remaining_min=0 auto_expire="false" message="Inattivo"
    local now
    now=$(now_epoch)

    # === MISURAZIONE DIRETTA DEI DEVICE (realtà, NON STATE_FILE) =============
    # 1. Telefono su Debian? (interfaccia enx attiva con IPv4)
    local debian_phone_if=""
    for ifc in $(ip -br link 2>/dev/null | awk '{print $1}'); do
        [[ "$ifc" =~ ^enx ]] || continue
        if ip link show "$ifc" >/dev/null 2>&1 && ip -4 addr show dev "$ifc" 2>/dev/null | grep -q 'inet '; then
            debian_phone_if="$ifc"; break
        fi
    done
    # 2. Router default route (misura reale via SSH)
    local router_route="" router_ok=false
    if router_ssh "true" >/dev/null 2>&1; then
        router_ok=true
        router_route=$(router_ssh "ip route show default 2>/dev/null" 2>/dev/null | head -1)
    fi

    # === DETERMINA STATO REALE (la realtà vince sullo STATE_FILE) ===========
    if $router_ok; then
        if [[ "$router_route" == *"usb0"* ]]; then
            # Normale: il router esce dal tethering USB del Note 11 sul router.
            state="idle"; mode="server"
            message="Normale: router su WAN Note 11 (usb0)"
        elif [[ "$router_route" == *"192.168.0.3"* ]]; then
            # Anchor Intranet presente sul router.
            if [[ -n "$debian_phone_if" ]]; then
                # Intranet ATTIVA: telefono su Debian + anchor presente.
                state="active"; mode="intranet"; phone_if="$debian_phone_if"
                phone_gw=$(ip -4 addr show dev "$debian_phone_if" 2>/dev/null | grep -oE 'inet [0-9.]+' | awk '{print $2}')
                message="Attivo via ${debian_phone_if} (intranet: LAN via Debian)"
            else
                # Anchor Intranet presente ma telefono su Debian ASSENTE: STALE.
                # Realtà: il tethering è morto. Segnala errore ma usa dati diretti.
                state="error"; mode="intranet"
                message="Anchor Intranet presente ma telefono su Debian assente: eseguire restore o riattivare il tethering USB."
            fi
        elif [[ -z "$router_route" ]]; then
            state="error"; mode="server"
            message="Router isolato: nessuna default route verso Internet."
        else
            state="error"; mode="server"
            message="Rotta primaria sconosciuta: $router_route"
        fi
    else
        # Router NON raggiungibile: impossibile misurare la realtà -> FALLBACK STATE_FILE.
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
            message="Router non raggiungibile: stato da STATE_FILE (fallback)"
        else
            state="error"; mode="server"
            message="Router non raggiungibile e nessuno STATE_FILE: impossibile determinare lo stato."
        fi
    fi

    # === FALLBACK STATE_FILE per metadati (solo se coerente con la realtà) ===
    # Se lo STATE_FILE esiste e descrive lo STESSO stato misurato, usa i suoi
    # timestamp (active_since, expire_at) e l'eventuale phone_if non rilevato.
    if [ -f "$STATE_FILE" ] && [[ "$state" != "error" ]]; then
        local sf_state sf_mode sf_phone_if sf_expire sf_activated
        sf_state=$(grep -E '^state=' "$STATE_FILE" | cut -d= -f2-)
        sf_mode=$(grep -E '^mode=' "$STATE_FILE" | cut -d= -f2-)
        sf_phone_if=$(grep -E '^phone_if=' "$STATE_FILE" | cut -d= -f2-)
        sf_expire=$(grep -E '^expire_at=' "$STATE_FILE" | cut -d= -f2-)
        sf_activated=$(grep -E '^activated_at=' "$STATE_FILE" | cut -d= -f2-)
        if [[ "$state" == "$sf_state" ]] && [[ "$mode" == "$sf_mode" ]]; then
            [ -n "$sf_activated" ] && active_since="$sf_activated"
            if [ -n "$sf_expire" ]; then
                remaining_min=$(( (sf_expire - now) / 60 ))
                [ "$remaining_min" -lt 0 ] && remaining_min=0
                auto_expire="true"
            fi
            [[ -z "$phone_if" ]] && [[ -n "$sf_phone_if" ]] && phone_if="$sf_phone_if"
        fi
        # Se la realtà è idle (Normale) ma STATE_FILE dice active: STATO_FILE STALE.
        # La realtà ha gia' vinto (state=idle sopra). Non rimuoviamo qui (solo lettura),
        # ma segnaliamo che il file e' inconsistente.
        if [[ "$state" == "idle" ]] && [[ "$sf_state" == "active" ]]; then
            message="Normale (router su usb0): STATE_FILE obsoleto ignorato."
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

# --- _netstat (interno) -----------------------------------------------------
# Dump diagnostico di iptables e route, eseguito come root via sudoers.
cmd_netstat() {
    echo "=== ip route ==="
    ip route show
    echo ""
    echo "=== ip rule ==="
    ip rule show
    echo ""
    echo "=== iptables FORWARD ==="
    iptables -L FORWARD -v -n --line-numbers 2>/dev/null
    echo ""
    echo "=== iptables NAT POSTROUTING ==="
    iptables -t nat -L POSTROUTING -v -n --line-numbers 2>/dev/null
    echo ""
    echo "=== ip_forward ==="
    cat /proc/sys/net/ipv4/ip_forward
}

# --- renat ------------------------------------------------------------------
# Ri-applica le regole iptables NAT/FORWARD leggendo lo stato salvato.
# Utile quando le regole vengono perse senza dover fare restore+re-activate.
# Idempotente: le regole vengono aggiunte solo se non gia' presenti.
cmd_renat() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "ERRORE: nessuno stato attivo (state file assente)." >&2
        return 1
    fi
    local phone_if mode
    phone_if=$(grep -E '^phone_if=' "$STATE_FILE" | cut -d= -f2-)
    mode=$(grep -E '^mode=' "$STATE_FILE" | cut -d= -f2-)
    if [ -z "$phone_if" ]; then
        echo "ERRORE: phone_if non trovato nello stato." >&2
        return 1
    fi
    echo "Ri-applicazione NAT/FORWARD su $phone_if (modalita: $mode)..."
    enable_nat_router "$phone_if"
    echo "OK: regole NAT/FORWARD ripristinate su $phone_if."
    # In modalita intranet, garantisce anche che la WAN del router sia abbattuta
    # (netifd puo' riportarla su autonomamente dopo un evento USB/carrier).
    if [ "$mode" = "intranet" ]; then
        echo "Modalita INTRANET: verifica WAN router..."
        local wan_active
        wan_active=$(ssh -i "$ROUTER_SSH_KEY" \
            -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
            -o ConnectTimeout=5 -o BatchMode=yes \
            root@"$ROUTER_IP" "ip route show default dev $ROUTER_WAN_IF metric 10 2>/dev/null | wc -l" 2>/dev/null | tr -d '[:space:]')
        if [ "${wan_active:-0}" -gt 0 ] 2>/dev/null; then
            echo "WAN router ancora attiva (netifd l'ha riportata su) - abbattimento..."
            router_wan_down
        else
            echo "WAN router gia' abbattuta - nessun intervento necessario."
        fi
    fi
}

# --- main -------------------------------------------------------------------
case "${1:-status}" in
    detect)      cmd_detect ;;
    activate)    shift; cmd_activate "$@" ;;
    rndis_activate) shift; cmd_rndis_activate "$@" ;;
    restore)     cmd_restore ;;
    status)      cmd_status ;;
    renat)       cmd_renat ;;
    diagnose)    cmd_diagnose ;;
    force_activate) shift; rm -f "$STATE_FILE" "$PID_FILE" 2>/dev/null; cmd_activate "$@" ;;
    _netstat)    cmd_netstat ;;
    _wan_down)   router_wan_down ;;
    _wan_up)     router_wan_up ;;
    _watch)      shift; cmd_watch "$@" ;;
    _drain)      shift; cmd_drain "$@" ;;
    *)
        echo "Uso: $0 {detect|activate [max_min] [intranet|server]|rndis_activate [max_min] [intranet|server]|restore|renat|status|diagnose|force_activate}" >&2
        exit 64
        ;;
esac
