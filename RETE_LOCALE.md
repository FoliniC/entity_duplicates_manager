# Architettura della Rete Locale

Documentazione della configurazione di rete per l'ambiente Home Assistant.

## Dispositivi Principali

### Server Home Assistant (Host)
- **Sistema Operativo:** Debian 13
- **Indirizzo IP:** `192.168.0.3`
- **Servizi:**
  - **Home Assistant:** Core della domotica.
  - **AdGuard Home:** Gestione DNS e DHCP per l'intera rete.

### Router (Gateway & Internet)
- **Hardware:** TP-Link AC1750 C7
- **Firmware:** OpenWrt 24.10 (LuCI)
- **Indirizzo IP:** `192.168.0.11`
- **Accesso:** SSH abilitato.
- **Funzione:** Accesso a Internet e routing locale.

### Desktop
- **Sistema Operativo:** Windows 11
- **Indirizzo IP:** `192.168.0.8`
- **Uso:** Workstation principale.

### Sistema Wi-Fi Mesh
- **Hardware:** Tenda AC1200 Mesh5 (MW5)
- **Configurazione:**
  - **Base (Cucina):**
    - **IP:** `192.168.0.10`
    - **Firmware:** `V1.0.0.33(6048)`
    - **MAC LAN:** `CC:2D:21:27:28:68` (Collegata via Ethernet al router)
    - **MAC WAN:** `CC:2D:21:27:28:6F`
    - **MAC Wi-Fi 2.4GHz:** `CC:2D:21:27:28:69`
    - **MAC Wi-Fi 5GHz:** `CC:2D:21:27:28:6C`
  - **Satellite 1 (Camera):** Collegamento mesh wireless.
  - **Satellite 2 (Balcone):** Collegamento mesh wireless.
- **Funzione:** Estensione della copertura Wi-Fi per aree non raggiunte direttamente dal router.
- **Canale 2.4GHz:** Automatico su **Canale 6** (non-overlapping con il **Canale 1** del router OpenWrt, evita roaming instabile dei dispositivi Tuya). Vedi [`tuya_handshake.md`](./tuya_handshake.md#6-ottimizzazione-wi-fi-e-roaming-prevenzione-wake-up-failed-e-heartbeat-timeout) per heartbeat timeout e gestione canali.

### Dispositivi IoT (Amazon Echo)
- **alexa-cucina**
  - **IP:** `192.168.0.90`
  - **MAC:** `68:f6:3b:c3:cb:7e`
- **alexa-camera**
  - **IP:** `192.168.0.89`
  - **MAC:** `68:f6:3b:99:6b:a3`

## Analisi Impatto Mesh e Ottimizzazione Canali (Alexa & Tuya)
L'integrazione del sistema Tenda Mesh5 e la gestione dei canali su OpenWrt hanno portato alla seguente configurazione ottimizzata:

1.  **Backhaul Ethernet:** La base in cucina collegata via cavo garantisce prestazioni elevate per l'area giorno.
2.  **Ottimizzazione alexa-camera:**
    *   **Stato:** Forzata sulla **5GHz** del router OpenWrt.
    *   **Configurazione:** Inserita in **Blacklist** sulla 2.4GHz del router e sul sistema Tenda Mesh.
    *   **Performance:** Bitrate rilevato ~**260 MBit/s** (VHT80), segnale **-65 dBm** (SNR 43). Questo garantisce una banda passante molto superiore alla 2.4GHz e una latenza ridotta.
3.  **Ottimizzazione alexa-cucina:**
    *   **Stato:** Agganciata alla base Tenda Mesh (cablata).
    *   **Configurazione:** Inserita in **Blacklist** su OpenWrt (sia 2.4GHz che 5GHz) per forzare il collegamento al sistema Mesh locale e prevenire instabilità dovute a "missing ACKs".
4.  **Interferenza Canali 5GHz:** Il router OpenWrt utilizza il **canale 149 (5GHz)** in modalità **VHT80** (fisso), mentre il Tenda Mesh opera sui canali bassi (es. 40), eliminando le sovrapposizioni.
5.  **Interferenza Canali 2.4GHz & Stabilità Tuya:**
    *   **Configurazione:** Il router OpenWrt è impostato sul **Canale 1 (2.4GHz)** fisso, mentre il sistema Tenda Mesh opera sul **Canale 6 (2.4GHz)** (gestito automaticamente dal Tenda) per eliminare le sovrapposizioni di banda 2.4GHz (canali non-overlapping 1 e 6).
    *   **Mitigazione Roaming Tuya:** Il MAC address di `luci-cucina` (`50:8b:b9:44:fe:4e`, IP `192.168.0.25`) non e' piu' in blacklist sulla 2.4GHz del router OpenWrt. Il dispositivo puo' quindi associarsi anche all'AP OpenWrt; l'accesso WAN resta limitato dalle regole Tuya selettive. Maggiori dettagli in [tuya_handshake.md](file:///home/carlo/docker/homeassistant/config/tuya_handshake.md#L45-L60).L60).

## Note di Configurazione
- Il server Debian (`192.168.0.3`) funge da centro di controllo sia per la domotica che per i servizi di rete critici (DNS/DHCP tramite AdGuard).
- L'accesso al router OpenWrt è possibile via Web UI (LuCI) o terminale (SSH).

## Monitoraggio del Traffico di Rete

Per diagnosticare rallentamenti e identificare dispositivi che saturano la banda, è stato implementato un sistema di monitoraggio integrato.

### Componenti del Sistema
1.  **Router (Data Source):**
    *   **Servizio:** `nlbwmon` installato sul TP-Link Archer C7.
    *   **Funzione:** Tiene traccia del traffico (byte/pacchetti) per ogni MAC/IP della rete.
    *   **Accesso:** SSH abilitato con chiave dedicata in `/config/.ssh/router_key`.
    *   **Configurazione Ottimizzata (Giugno 2026):**
        - **Commit Interval:** Impostato a `1m` (in RAM) per avere dati quasi real-time.
        - **Flow Offloading:** Disattivato (`flow_offloading='0'`, `flow_offloading_hw='0'`). Questa modifica è necessaria perché l'offloading accelera il traffico bypassando i contatori della CPU, rendendo invisibile il traffico dei dispositivi collegati tramite bridge/mesh (es. Alexa in cucina).
2.  **Server HA (Integrazione Avanzata):**
    *   **Monitoraggio Qualità (Livello 1):** `helpers/network_quality.py` (ogni 60s). Misura **Packet Loss**, **Jitter** e **Latenza** tramite ping sequenziali.
    *   **Watchdog Tunnel Cloudflare (Livello 1.5):** `packages/cloudflare_watchdog.yaml`. Controlla ogni 60s la raggiungibilità dell'URL esterno (`https://home.vialeformica.org`). Se l'URL non risponde per oltre **5 minuti**, il sistema esegue automaticamente il riavvio del container `cloudflare-tunnel` tramite SSH sul server host.
        - **Container atteso:** `cloudflare-tunnel` sul server Docker `192.168.0.3`.
        - **Comandi HA:** `yaml_generator/shell_command/cloudflare.yaml` esegue `docker start|stop|restart cloudflare-tunnel` via SSH usando `/config/.ssh/host_key`.
        - **Ricreazione se il container viene perso:** recuperare il token da Cloudflare Dashboard -> Zero Trust -> Networks -> Tunnels, oppure dal link diretto `https://dash.cloudflare.com/929828bf22cac620ccecfb4f126da3de/tunnels`. Selezionare il tunnel di `home.vialeformica.org` -> Overview -> Add a replica. Copiare il comando `cloudflared tunnel run --token ...` e usare solo il token.
        - **Comando Docker di ripristino:**
          ```bash
          docker run -d \
            --name cloudflare-tunnel \
            --restart unless-stopped \
            --network host \
            cloudflare/cloudflared:latest \
            tunnel --no-autoupdate run --token '<TOKEN_DA_CLOUDFLARE>'
          ```
        - **Verifica:** `docker logs --tail 120 cloudflare-tunnel` deve mostrare `Registered tunnel connection` e la config remota `home.vialeformica.org -> http://192.168.0.3:8123`. Da Home Assistant, `curl -I https://home.vialeformica.org` deve restituire `HTTP/2 200`.
        - **Nota backup:** il backup Home Assistant contiene watchdog e shell command, ma non contiene i container Docker. Il backup GitHub genera una copia sanitizzata del compose host in `host_backup/docker-compose.yml`.
    *   **Velocità WAN (Livello 2):** `helpers/wan_traffic_realtime.py` (ogni 10s). Legge `/proc/net/dev` per la banda totale istantanea e calcola la **Saturazione %**.
    *   **Real-time Per-Device (Livello 3):** `helpers/realtime_per_device.py` (ogni 15s). Utilizza **nftables accounting** sul router per tracciare la banda dei dispositivi critici (Desktop, Alexa, HA).
    *   **Diagnosi Automatica:** Package `packages/network_diagnosis.yaml`. Un sensore template (`sensor.network_status_diagnosis`) incrocia i dati dei tre livelli per identificarle se eventuali rallentamenti sono causati dalla linea o dalla saturazione locale.
    *   **Boost Mode:** Sistema per aumentare temporaneamente la frequenza di campionamento tramite `input_boolean.network_boost_mode`. La durata e l'intervallo (2-15s) sono configurabili dall'utente.
        - *Nota tecnica:* Grazie all'implementazione di **SSH Multiplexing (ControlMaster)**, la sessione rimane aperta per tutta la durata del boost. Questo azzera l'overhead di connessione/autenticazione, rendendo l'intervallo di 2s estremamente leggero per la CPU del router.

3.  **Dashboard di Controllo:**
    *   **Visualizzazione:** Dashboard "Traffico internet" a due colonne.
    *   **Funzionalità:**
        - **Colonna Sinistra:** Diagnosi automatica, indicatori di qualità (Loss/Jitter), saturazione e riepilogo storico (nlbwmon).
        - **Colonna Destra:** Andamento real-time grafico e tabella "Chi sta usando banda ORA?" (dati nftables).
        - **Interattività:** Tutte le card supportano la selezione del testo per l'esportazione manuale dei dati.

### Configurazione Grafico Top 5 Dispositivi
...
---
*Ultimo aggiornamento: 10 Giugno 2026*
1.  **Sensori Template** (`/config/packages/network_monitoring.yaml`): Sono definiti 5 sensori individuali (`top_device_1_mb` ... `top_device_5_mb`). 
    - **Nome statico**: "Top Device X MB" per un'identificazione univoca nel database.
    - **Stato**: Valore numerico del traffico (MB).
    - **Attributo `device_name`**: Contiene il nome dinamico del dispositivo.

2.  **ApexCharts Card** (`/config/dashboards/internet_traffic.yaml`): Visualizza i 5 sensori come serie individuali in modalità minimale.
    ```yaml
    series:
      - entity: sensor.top_device_1_mb
      - entity: sensor.top_device_2_mb
      - entity: sensor.top_device_3_mb
      - entity: sensor.top_device_4_mb
      - entity: sensor.top_device_5_mb
    ```

3.  **Vantaggi:** 
    - **Massima Compatibilità**: Non usa script JavaScript né template nella card, rendendola immune a problemi di timing o versioning del frontend.
    - **Stabilità dei Dati**: I sensori hanno stati numerici standard, ideali per la gestione dello storico di HA.

---
*Ultimo aggiornamento: 25 Luglio 2026*

## Collegamento SSH tra Server

Il server Debian (192.168.0.3) funge da pivot per la gestione remota degli altri dispositivi di rete tramite SSH. Le chiavi sono nel container HA (`/config/.ssh/`) e montate anche sul filesystem host (`/home/carlo/docker/homeassistant/config/.ssh/`).

### Chiavi SSH disponibili

| Chiave | Formato | Utilizzo | Host |
|---|---|---|---|
| `host_key` | RSA 4096 | Loopback locale (Debian) | `carlo@localhost` (via sudo) |
| `router_key` | (inherited) | Router OpenWrt | `root@192.168.0.11` |
| `win_key` | ED25519 | PC Windows 11 | `carlo_2@192.168.0.8` |

### Comandi di collegamento

**Router OpenWrt (192.168.0.11):**
```bash
ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11
```

**Server Debian locale (loopback):**
```bash
ssh -i /config/.ssh/host_key -o StrictHostKeyChecking=no carlo@localhost
```

**PC Windows 11 (192.168.0.8):**
```bash
ssh -i /config/.ssh/win_key -o StrictHostKeyChecking=no carlo_2@192.168.0.8
```

### Script di tethering USB
 
 Entrambi i server host supportano lo script di tethering USB:
 
 | Server | Script | Path remoto |
 |---|---|---|
 | Debian (192.168.0.3) | `usb_tether.sh` (bash) | `/home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh` |
 | Windows (192.168.0.8) | `usb_tether.ps1` (PowerShell) | `C:\Scripts\usb_tether.ps1` |
 
 **Architettura attuale (Agosto 2026):**
 
 Il package Home Assistant (`packages/usb_tether.yaml`) delega tutta la logica SSH a uno **script helper unificato** (`/config/helpers/usb_tether_ha.sh`) che gira nel container HA. Questo script:
 - Usa **SSH Multiplexing** (`ControlMaster=auto`, `ControlPersist=60s`) su tutte le connessioni (Debian, Windows, Router) per eliminare l'overhead di handshake.
 - Esegue comandi **async**: ritorna subito `{"state":"activating",...}` / `{"state":"restoring",...}` mentre il lavoro prosegue in background.
 - Chiama gli script nativi sui due host:
   - **Debian**: `/home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh` (bash)
   - **Windows**: `C:\Scripts\usb_tether.ps1` (PowerShell)
 - Gestisce lato **router OpenWrt** le transizioni graceful con **CONNMARK + ip rule table 88**:
   - **Attivazione intranet (Windows)**: mantiene la WAN router `usb0 metric 10` per `ACTIVATE_GRACE_SECONDS` (default 120s), poi la rimuove in background (`router_cutover_windows`).
   - **Restore (Windows)**: marca le connessioni ESTABLISHED/RELATED in ingresso su `br-lan` con mark `0x88`, le dirotta via tabella 88 verso l'IP Windows per `RESTORE_GRACE_SECONDS` (default 180s), poi pulisce mark/regole/tabella in background (`router_finish_restore_windows`).
   - **Debian**: logica invariata (watchdog detached + route metric 50/100 + NAT router).
 
 **Comandi disponibili da Home Assistant (via shell_command):**
 
 ```yaml
 shell_command:
   usb_tether_activate: >
     /config/helpers/usb_tether_ha.sh activate server "{{ states('input_select.usb_tether_host') }}" "{{ states('input_number.usb_tether_max_duration') | int(60) }}"
   usb_tether_activate_intranet: >
     /config/helpers/usb_tether_ha.sh activate intranet "{{ states('input_select.usb_tether_host') }}" "{{ states('input_number.usb_tether_max_duration') | int(60) }}"
   usb_tether_restore: >
     /config/helpers/usb_tether_ha.sh restore server "{{ states('input_select.usb_tether_host') }}" "{{ states('input_number.usb_tether_max_duration') | int(60) }}"
 ```
 
 **Sensori:**
 - `sensor.usb_tether_status` (command_line, poll 30s): stato JSON + attributi (mode, phone_if, phone_gw, remaining_min, active_since, auto_expire, message)
 - `sensor.usb_tether_log` (command_line, poll 15s, python3 `/config/helpers/read_usb_tether_log.py`): espone il log file `/config/logs/usb_tether/usb_tether.log` con attributi `line_count`, `updated`, `text`, `lines`
 
 **Dashboard "Tethering USB" (`dashboards/internet_traffic.yaml`, path `tethering-usb`):**
 - Banner stato colorato (verde/arancio/rosso/grigio) con auto-ripristino countdown
 - 3 bottoni: 🔄 Normale (restore), 📱 Server (activate server), 🌐 Intranet (activate intranet)
 - 🔴 EMERGENCY RESTORE: chiama direttamente `shell_command.usb_tether_restore` bypassando script/logica
 - Textbox log con timestamp, contatore righe, ultimo aggiornamento, contenuto completo (monospace, pre-wrap)
 - Dettagli sensore, selezione host (Debian/Windows), durata safety-net
 
---
*Ultimo aggiornamento: 14 Agosto 2026*

### Controllo e Riattivazione Tethering USB via ADB (OpenWrt Router)
Sul router OpenWrt (`192.168.0.11`) è stato installato l'ambiente **ADB nativo (MIPS)** per la gestione automatica del telefono Android (Redmi Note 11 Pro 5G) collegato alla porta USB del router:
- **Pacchetti ADB locali:** `/etc/adb_pkgs/adb.ipk` e `/etc/adb_pkgs/libcrypto.ipk` (conservati in flash, decompressi in RAM all'esecuzione per non saturare la ROM).
- **Wrapper ADB:** `/usr/bin/adb_router` (esegue ADB su architettura MIPS caricando le librerie da RAM).
- **Script di riattivazione:** `/usr/bin/enable_usb_tether.sh` (forza lo switch automatico del telefono a modalità RNDIS/Tethering USB via ADB).
- **Hotplug USB:** `/etc/hotplug.d/usb/99-usb-tethering` (riattiva automaticamente il tethering ad ogni ricollegamento USB o reboot).

**Comando di ripristino manuale da HA / SSH Router:**
```bash
ssh -i /config/.ssh/router_key root@192.168.0.11 "/usr/bin/enable_usb_tether.sh"
```

---
*Ultimo aggiornamento: 1 Agosto 2026 (commit 28a1b44)*

### Note di sicurezza
- Le chiavi sono NON password-protette (uso automation).
- Il file `host_key` è usato anche per il ControlMaster SSH Multiplexing.
- `win_key` è stata generata appositamente per Windows (formato ED25519, più compatibile con OpenSSH for Windows 9.5).
- Il router accetta solo connessioni SSH chiave, password disabilitata.

## Sorgenti Script Tethering USB

### `usb_tether.sh` (Debian 13 — `/home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh`)

```bash
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

# Toglie/ripristina la WAN primaria del router (usb0) per forzare tutto il traffico via server.
router_wan_down() {
    router_ssh "ip route del default via 10.175.108.144 dev usb0 metric 10 2>/dev/null; true" \
        && echo "WAN router disattivata (route usb0 rimossa)." \
        || echo "WARN: WAN router gia assente o errore." >&2
}

router_wan_up() {
    router_ssh "ip route replace default via 10.175.108.144 dev usb0 metric 10 2>/dev/null; true" \
        && echo "WAN router riattivata (route usb0 ripristinata)." \
        || echo "WARN: impossibile ripristinare WAN router." >&2
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
```

### `usb_tether.ps1` (Windows 11 — `C:\Scripts\usb_tether.ps1`)

```powershell
#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Gestione tethering USB come default route temporanea per Windows 11.
.DESCRIPTION
    Permette di instradare il traffico Internet della LAN verso un telefono
    collegato in USB tethering sul PC Windows. Abilita NAT e routing.
    In modalità intranet disabilita la WAN del router OpenWrt e aggiunge
    una route di fallback sul router verso questo server Windows.

    Uso:
        .\usb_tether.ps1 -Action detect
        .\usb_tether.ps1 -Action activate -MaxMinutes 60 [-Mode intranet|server]
        .\usb_tether.ps1 -Action restore
        .\usb_tether.ps1 -Action status
        .\usb_tether.ps1 -Action diagnose
.NOTES
    DEVE essere eseguito come Administrator.
    Richiede: OpenSSH Server attivo, NetNat module.
#>

param(
    [ValidateSet('detect','activate','restore','status','diagnose')]
    [string]$Action = 'status',
    [int]$MaxMinutes = 30,
    [ValidateSet('server','intranet')]
    [string]$Mode = 'intranet'
)

# --- Costanti ---
$LAN_NET = '192.168.0.0/24'
$LAN_GW = '192.168.0.11'          # IP router OpenWrt (gateway LAN)
$ROUTER_IP = '192.168.0.11'
$ROUTER_USER = 'root'
$ROUTER_KEY = 'C:\Users\carlo_2\.ssh\router_key'
$NAT_NAME = 'USBTetherNAT'
$STATE_DIR = Join-Path $env:LOCALAPPDATA 'usb_tether'
$STATE_FILE = Join-Path $STATE_DIR 'usb_tether_state.json'
$WATCHDOG_JOB_NAME = 'USBTetherWatchdog'

# --- Funzioni helper ---
function Get-NowEpoch { [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds() }
function Get-NowIso  { Get-Date -Format 'yyyy-MM-dd HH:mm:ss' }
function Write-Log   { param($Msg) Write-Host "[$(Get-NowIso)] $Msg" }
function EpochTo-DateTime {
    param([int]$Epoch)
    return (Get-Date "1970-01-01 00:00:00Z").AddSeconds($Epoch).ToLocalTime()
}

# --- Rileva interfaccia LAN dinamicamente ---
function Get-LanInterface {
    $adapters = Get-NetAdapter | Where-Object { 
        $_.Status -eq 'Up' -and 
        $_.InterfaceAlias -notmatch 'Wi-Fi|WiFi|Wireless|Loopback|Virtual|Bluetooth|vEthernet|Docker|isatap|Teredo'
    }
    foreach ($adapter in $adapters) {
        $ipConfig = Get-NetIPConfiguration -InterfaceIndex $adapter.InterfaceIndex
        $ipv4 = $ipConfig.IPv4Address.IPAddress
        if ($ipv4 -is [array]) { $ipv4 = $ipv4[0] }
        if ($ipv4 -and ($ipv4 -match '^192\.168\.0\.')) {
            return $adapter.InterfaceAlias
        }
    }
    # Fallback: prima interfaccia UP non-WiFi
    return ($adapters | Select-Object -First 1).InterfaceAlias
}

# Imposta $LAN_IF_NAME dinamicamente
$script:LAN_IF_NAME = Get-LanInterface
if (-not $script:LAN_IF_NAME) {
    Write-Warning "Impossibile rilevare interfaccia LAN automaticamente. Uso 'Ethernet' come fallback."
    $script:LAN_IF_NAME = 'Ethernet'
}
Write-Log "Interfaccia LAN rilevata: $script:LAN_IF_NAME"

# --- Verifica permessi chiave SSH router ---
function Test-RouterKeyPermissions {
    if (-not (Test-Path $ROUTER_KEY)) {
        Write-Warning "Chiave router NON trovata: $ROUTER_KEY"
        Write-Warning "Copiala da Debian: scp /config/.ssh/router_key carlo_2@192.168.0.8:C:\Users\carlo_2\.ssh\router_key"
        return $false
    }
    try {
        $acl = Get-Acl $ROUTER_KEY
        $access = $acl.Access | Where-Object { 
            $_.IdentityReference -notmatch '^BUILTIN\\Administrators$|^NT AUTHORITY\\SYSTEM$|^carlo_2$' 
        }
        if ($access) {
            Write-Warning "Permessi chiave SSH troppo aperti. Correggi con:"
            Write-Warning "  icacls $ROUTER_KEY /inheritance:r /grant:r `$env:USERNAME`:R"
        }
    } catch {
        Write-Warning "Impossibile verificare permessi chiave: $_"
    }
    return $true
}

# --- SSH al router ---
function Router-SSH {
    param([string]$Command)
    if (-not (Test-Path $ROUTER_KEY)) {
        Write-Warning "Chiave router non trovata: $ROUTER_KEY"
        return $false
    }
    $sshCmd = "ssh -i $ROUTER_KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=QUIET -o ConnectTimeout=5 $ROUTER_USER@$ROUTER_IP '$Command'"
    $result = Invoke-Expression $sshCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Router SSH fallito: $result"
        return $false
    }
    return $true
}

# --- Aggiunge route fallback sul router via Windows (metric 30) ---
function Add-RouterFallbackRoute {
    Write-Log "Aggiungo route fallback sul router via $LAN_GW (Windows metric 30)..."
    $cmd = "ip route replace default via $LAN_GW dev br-lan metric 30 2>/dev/null; true"
    return Router-SSH -Command $cmd
}

# --- Rimuove route fallback dal router ---
function Remove-RouterFallbackRoute {
    Write-Log "Rimuovo route fallback dal router..."
    $cmd = "ip route del default via $LAN_GW dev br-lan metric 30 2>/dev/null; true"
    return Router-SSH -Command $cmd
}

# --- Disabilita WAN router (rimuove route default via usb0 metric 10) ---
function Disable-RouterWAN {
    Write-Log "Disabilito WAN router (rimuovo route usb0 metric 10)..."
    $cmd = "ip route del default dev usb0 metric 10 2>/dev/null; true"
    return Router-SSH -Command $cmd
}

# --- Riabilita WAN router (ripristina route default via usb0 metric 10) ---
function Enable-RouterWAN {
    Write-Log "Riabilito WAN router (ripristino route usb0 metric 10)..."
    $cmd = "ip route replace default via 10.175.108.144 dev usb0 metric 10 2>/dev/null; true"
    return Router-SSH -Command $cmd
}

# --- Rileva interfaccia telefono ---
function Get-PhoneInterface {
    $configs = Get-NetIPConfiguration -Detailed 2>$null | Where-Object {
        $_.NetAdapter.Status -eq 'Up' -and
        $_.InterfaceAlias -notmatch 'Loopback|Virtual|Bluetooth|vEthernet|Docker|isatap|Teredo' -and
        $_.InterfaceAlias -ne $script:LAN_IF_NAME -and
        $_.IPv4DefaultGateway -ne $null
    }
    foreach ($cfg in $configs) {
        $gw = $cfg.IPv4DefaultGateway.NextHop
        if ($gw -and ($gw -notmatch '^192\.168\.0\.')) {
            $ip = $cfg.IPv4Address.IPAddress
            if ($ip -is [array]) { $ip = $ip[0] }
            return @{
                InterfaceAlias = $cfg.InterfaceAlias
                InterfaceIndex = $cfg.InterfaceIndex
                Gateway        = $gw
                IPAddress      = $ip
            }
        }
    }
    return $null
}

# --- Abilita NAT e routing ---
function Enable-TetherNAT {
    param($PhoneIface)
    Write-Log "Abilito forwarding su $script:LAN_IF_NAME..."
    Set-NetIPInterface -InterfaceAlias $script:LAN_IF_NAME -Forwarding Enabled -ErrorAction SilentlyContinue

    Write-Log "Abilito forwarding su $($PhoneIface.InterfaceAlias)..."
    Set-NetIPInterface -InterfaceAlias $PhoneIface.InterfaceAlias -Forwarding Enabled -ErrorAction SilentlyContinue

    # Rimuovi qualsiasi NAT esistente sullo stesso prefisso interno
    Get-NetNat | Where-Object { $_.InternalIPInterfaceAddressPrefix -eq $LAN_NET } |
        Remove-NetNat -Confirm:$false -ErrorAction SilentlyContinue

    Write-Log "Creo NAT per $LAN_NET (uscita automatica via routing table)..."
    New-NetNat -Name $NAT_NAME -InternalIPInterfaceAddressPrefix $LAN_NET -ErrorAction Stop | Out-Null

    Write-Log "NAT attivato."
}

# --- Disabilita NAT ---
function Disable-TetherNAT {
    Write-Log "Rimuovo NAT..."
    Get-NetNat -Name $NAT_NAME -ErrorAction SilentlyContinue | Remove-NetNat -Confirm:$false -ErrorAction SilentlyContinue

    Write-Log "Disabilito forwarding su $script:LAN_IF_NAME..."
    Set-NetIPInterface -InterfaceAlias $script:LAN_IF_NAME -Forwarding Disabled -ErrorAction SilentlyContinue
    Write-Log "NAT disattivato."
}

# --- Watchdog: auto-restore allo scadere del tempo ---
function Start-Watchdog {
    param($ExpireEpoch)
    # Rimuovi job esistente se presente
    Get-Job -Name $WATCHDOG_JOB_NAME -ErrorAction SilentlyContinue | Remove-Job -Force

    $scriptBlock = {
        param($ExpireEpoch, $StateFile)
        while ($true) {
            $now = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            if ($now -ge $ExpireEpoch) {
                Write-Host "[Watchdog] Tempo scaduto, eseguo restore automatico..."
                & "$PSScriptRoot\usb_tether.ps1" -Action restore
                break
            }
            if (-not (Test-Path $StateFile)) {
                Write-Host "[Watchdog] File stato rimosso, esco."
                break
            }
            Start-Sleep -Seconds 15
        }
    }
    Start-Job -Name $WATCHDOG_JOB_NAME -ScriptBlock $scriptBlock -ArgumentList $ExpireEpoch, $STATE_FILE | Out-Null
    Write-Log "Watchdog avviato (scadenza: $(EpochTo-DateTime $ExpireEpoch))"
}

function Stop-Watchdog {
    Get-Job -Name $WATCHDOG_JOB_NAME -ErrorAction SilentlyContinue | Remove-Job -Force
    Write-Log "Watchdog fermato."
}

# --- detect ---
function cmd_detect {
    $phone = Get-PhoneInterface
    if ($phone) {
        "$($phone.InterfaceAlias)|$($phone.Gateway)"
        return
    }
    Write-Warning "Nessuna interfaccia telefono trovata."
    ""
}

# --- activate ---
function cmd_activate {
    # Verifica chiave SSH router
    if (-not (Test-RouterKeyPermissions)) {
        return 1
    }

    # Assicura directory stato
    if (-not (Test-Path $STATE_DIR)) {
        New-Item -ItemType Directory -Path $STATE_DIR -Force | Out-Null
    }

    if (Test-Path $STATE_FILE) {
        $st = Get-Content $STATE_FILE | ConvertFrom-Json
        if ($st.state -eq 'active') {
            Write-Warning "GIA' ATTIVO: usa -Action restore prima di riattivare."
            return 1
        }
    }

    $phone = Get-PhoneInterface
    if (-not $phone) {
        Write-Warning "Telefono USB non rilevato. Attiva il tethering sul cellulare."
        return 2
    }

    $now = Get-NowEpoch
    $expire = $now + ($MaxMinutes * 60)

    # Abilita NAT/forwarding
    try {
        Enable-TetherNAT -PhoneIface $phone
    } catch {
        Write-Error "Impossibile abilitare NAT: $_"
        return 3
    }

    # Se modalità intranet: disabilita WAN router E aggiungi route fallback
    if ($Mode -eq 'intranet') {
        $wanDisabled = $false
        if (-not (Disable-RouterWAN)) {
            Write-Warning "Impossibile disabilitare WAN router."
        } else {
            $wanDisabled = $true
        }
        if (-not (Add-RouterFallbackRoute)) {
            Write-Warning "Impossibile aggiungere route fallback sul router!"
            # Rollback: riabilita WAN se l'abbiamo disabilitata
            if ($wanDisabled) { Enable-RouterWAN }
            return 4
        }
    }

    # Salva stato
    $state = @{
        state         = 'active'
        mode          = $Mode
        phone_if      = $phone.InterfaceAlias
        phone_gw      = $phone.Gateway
        phone_ip      = $phone.IPAddress
        lan_gw        = $LAN_GW
        lan_if        = $script:LAN_IF_NAME
        activated_at  = $now
        expire_at     = $expire
        message       = "Attivo via $($phone.InterfaceAlias) ($Mode)"
    } | ConvertTo-Json -Compress
    $state | Set-Content $STATE_FILE -Force

    # Avvia watchdog per auto-restore
    Start-Watchdog -ExpireEpoch $expire

    Write-Host "OK attivato: $($phone.InterfaceAlias) via $($phone.Gateway) [$Mode] per ${MaxMinutes} min"
    return 0
}

# --- restore ---
function cmd_restore {
    $phoneIface = $null
    $wasIntranet = $false
    $lanIf = $script:LAN_IF_NAME
    if (Test-Path $STATE_FILE) {
        try {
            $st = Get-Content $STATE_FILE | ConvertFrom-Json
            $phoneIface = $st.phone_if
            $wasIntranet = ($st.mode -eq 'intranet')
            $lanIf = if ($st.lan_if) { $st.lan_if } else { $script:LAN_IF_NAME }
        } catch {}
    }

    # Ferma watchdog
    Stop-Watchdog

    # Disabilita NAT/forwarding
    Disable-TetherNAT

    # Se era intranet: PRIMA rimuovi route fallback, POI riabilita WAN router
    if ($wasIntranet) {
        if (-not (Remove-RouterFallbackRoute)) {
            Write-Warning "Impossibile rimuovere route fallback dal router."
        }
        if (-not (Enable-RouterWAN)) {
            Write-Warning "Impossibile riabilitare WAN router."
        }
    }

    # Pulisci stato
    if (Test-Path $STATE_FILE) { Remove-Item $STATE_FILE -Force -ErrorAction SilentlyContinue }

    Write-Host "OK ripristinato: route tornata alla LAN."
    return 0
}

# --- status ---
function cmd_status {
    $state = 'idle'
    $mode = ''
    $phone_if = ''
    $phone_gw = ''
    $lan_gw = $LAN_GW
    $lan_if = $script:LAN_IF_NAME
    $active_since = ''
    $remaining_min = 0
    $auto_expire = $false
    $message = 'Inattivo'

    if (Test-Path $STATE_FILE) {
        try {
            $st = Get-Content $STATE_FILE | ConvertFrom-Json
            $state = $st.state
            $mode = if ($st.mode) { $st.mode } else { 'intranet' }
            $phone_if = $st.phone_if
            $phone_gw = $st.phone_gw
            $lan_gw = $st.lan_gw
            $lan_if = if ($st.lan_if) { $st.lan_if } else { $script:LAN_IF_NAME }
            $active_since = $st.activated_at
            $now = Get-NowEpoch
            if ($st.expire_at) {
                $remaining_min = [Math]::Max(0, [int](($st.expire_at - $now) / 60))
                $auto_expire = $true
            }
            $message = if ($state -eq 'active') { "Attivo via $phone_if ($mode)" } else { $st.message }

            if ($state -eq 'active') {
                $nat = Get-NetNat -Name $NAT_NAME -ErrorAction SilentlyContinue
                if (-not $nat) {
                    $state = 'error'
                    $message = "Stato attivo ma NAT assente: eseguire restore."
                }
                # Verifica watchdog
                $job = Get-Job -Name $WATCHDOG_JOB_NAME -ErrorAction SilentlyContinue
                if (-not $job) {
                    $state = 'error'
                    $message += " Watchdog non in esecuzione."
                }
            }
        } catch {}
    }

    $since_human = ''
    if ($active_since -and $active_since -ne 0) {
        $since_human = (EpochTo-DateTime $active_since).ToString('yyyy-MM-dd HH:mm:ss')
    }

    $result = @{
        state         = $state
        mode          = $mode
        phone_if      = $phone_if
        phone_gw      = $phone_gw
        lan_gw        = $lan_gw
        lan_if        = $lan_if
        active_since  = $since_human
        remaining_min = $remaining_min
        auto_expire   = [bool]$auto_expire
        message       = $message
    }
    return ($result | ConvertTo-Json -Compress)
}

# --- diagnose ---
function cmd_diagnose {
    Write-Host "=== Interfacce di rete ==="
    Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Format-Table Name, Status, LinkSpeed

    Write-Host "`n=== IP Configurazione ==="
    Get-NetIPConfiguration | Where-Object {$_.NetAdapter.Status -eq 'Up'} | 
        Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway | Format-Table

    Write-Host "`n=== Route table (default) ==="
    Get-NetRoute -DestinationPrefix '0.0.0.0/0' | Format-Table DestinationPrefix, NextHop, InterfaceAlias, RouteMetric

    Write-Host "`n=== NAT rules ==="
    Get-NetNat -ErrorAction SilentlyContinue | Format-Table Name, InternalIPInterfaceAddressPrefix, ExternalIPInterfaceAddressPrefix

    $phone = Get-PhoneInterface
    if ($phone) {
        Write-Host "`n=== Telefono rilevato ==="
        $phone | Format-Table
    } else {
        Write-Host "`n=== NESSUN telefono rilevato ==="
    }

    Write-Host "`n=== Stato watchdog ==="
    Get-Job -Name $WATCHDOG_JOB_NAME -ErrorAction SilentlyContinue | Format-Table Id, Name, State, HasMoreData

    Write-Host "`n=== Chiave SSH router ==="
    Test-RouterKeyPermissions
    if (Test-Path $ROUTER_KEY) {
        $acl = Get-Acl $ROUTER_KEY
        $acl.Access | Format-Table IdentityReference, FileSystemRights, AccessControlType
    }
}

# --- MAIN ---
switch ($Action) {
    'detect'   { cmd_detect }
    'activate' { cmd_activate }
    'restore'  { cmd_restore }
    'status'   { cmd_status }
    'diagnose' { cmd_diagnose }
    default    { Write-Host "Uso: .\usb_tether.ps1 -Action {detect|activate|restore|status|diagnose} [-MaxMinutes N] [-Mode server|intranet]" }
}
```

---

## Mappatura Unità di Rete Z: (Windows)

**Data:** 9 Agosto 2026

L'unità di rete `Z:` è stata mappata su `\\192.168.0.3\config` (Home Assistant Config) tramite **Gestione Risorse / File Explorer** (GUI).

**Nota tecnica:** Il comando `net use` da terminale restituiva `Errore di sistema 67` ("Impossibile trovare il nome della rete") nonostante:
- Ping a `192.168.0.3` funzionasse correttamente
- `net view \\192.168.0.3` mostrasse la condivisione `config`
- Le credenziali per `carlo@192.168.0.3` fossero salvate in Credential Manager (`Domain:target=192.168.0.3`)

**Workaround usato:** Mappatura tramite interfaccia grafica (File Explorer → Questo PC → Connetti unità di rete) che ha funzionato correttamente al primo tentativo.

**Verifica:** `dir Z:` conferma l'accesso completo alla configurazione Home Assistant (es. `configuration.yaml`, `automations.yaml`, `packages/`, ecc.).

---

## Troubleshooting Passaggio Modalità "Normale" (16 Agosto 2026)

### Problema riscontrato

Il passaggio dalla modalità **Intranet** (tethering via Debian) alla modalità **Normale** (WAN via Redmi Note 11 Pro 5G → router OpenWrt) causava la **perdita totale di connettività** per tutti i dispositivi LAN (incluso Windows 11 `192.168.0.8`). Era necessario attivare "Intranet" due volte per ripristinare la connessione.

### Root Cause

Il problema è **duplice**:

#### 1. Android: NAT tethering desincronizzato

Il Redmi Note 11 Pro 5G (collegato via USB al router), pur mostrando l'interfaccia `usb0` attiva sul router e rispondendo ai ping interni (`10.16.x.x` → 2ms), **non instradava i pacchetti su internet**. Il demone di tethering Android si è desincronizzato: l'interfaccia RNDIS era up ma le regole `iptables` interne di Android per il NAT/forwarding non erano attive.

**Diagnostica chiave:**
```bash
# Dal router - il telefono risponde internamente ma non instrada:
ping -c 1 10.16.159.126      → OK (2ms)
ping -c 1 -I usb0 8.8.8.8   → 100% packet loss

# Via ADB - stato rete dati Android:
adb_router shell dumpsys telephony.registry | grep mDataConnectionState
# → mDataConnectionState=0  (DISCONNECTED)
```

**Cause possibili del desync Android:**
- Inattività prolungata del dispositivo (standby aggressivo MIUI)
- Disconnessione/riconnessione rapida dell'interfaccia USB durante i passaggi di modalità
- La MIUI gestisce il NAT tethering in modo non atomico con l'interfaccia RNDIS

**Fix temporaneo:** Toggle manuale "Tethering USB" in Impostazioni → Hotspot (spegni + riaccendi). Se non basta, riavvio completo del telefono.

#### 2. mwan3: `initial_state online` causa rotta immediata senza verifica

**mwan3** (multi-WAN manager installato sul router) aveva `initial_state 'online'` per l'interfaccia `wan`. Questo significa che al `ifup` di `usb0`, mwan3 inseriva immediatamente la rotta `default via usb0 metric 10` **senza aspettare l'esito del tracking** (ping verso `1.1.1.1`, `8.8.8.8`, ecc.). 

Poiché il tracking parte in parallelo, nei ~40 secondi necessari per le 8 conferme consecutive (`up '8'`), il router aveva già la rotta rotta come primaria e tutta la LAN perdeva internet.

**Stessa condizione si verificava anche nei test diagnostici**: il comando `ifdown wan / ifup wan` eseguito per diagnostica ha scatenato la reinserzione immediata della rotta.

### Soluzioni Applicate

#### Fix 1: mwan3 `initial_state offline`

```bash
uci set mwan3.wan.initial_state='offline'
uci commit mwan3
/etc/init.d/mwan3 restart
```

Con `initial_state 'offline'`, mwan3 NON inserisce la rotta al `ifup` ma aspetta che il tracking confermi la connettività (8 ping positivi × 5s = ~40s). Solo allora la rotta diventa attiva.

> **Nota:** mwan3 è configurato con `down '3'` e `up '8'` — tre ping falliti consecutivi bastano a dichiarare `wan offline` e rimuovere la rotta, otto positivi consecutivi per dichiararla `online`.

#### Fix 2: Hotplug guard `98-wan-verify`

Script installato in `/etc/hotplug.d/iface/98-wan-verify` sul router OpenWrt:

```sh
#!/bin/sh
# Verifica connettivita' usb0 prima di lasciare la rotta default attiva.
# Se il ping fallisce, rimuove la rotta: il fallback via br-lan (192.168.0.3)
# resta attivo e i client LAN non perdono internet.

[ "$ACTION" = "ifup" ] || exit 0
[ "$INTERFACE" = "wan" ] || exit 0

logger -t wan-verify "wan ifup su $DEVICE - verifica connettivita' usb0..."
sleep 3

if ping -c 3 -W 4 -I "$DEVICE" 8.8.8.8 > /dev/null 2>&1; then
    logger -t wan-verify "OK: usb0 raggiunge internet, rotta default mantenuta"
    exit 0
fi

logger -t wan-verify "WARN: usb0 non raggiunge internet - rimuovo rotta default"
while ip route del default dev "$DEVICE" 2>/dev/null; do :; done
logger -t wan-verify "Rotta default usb0 rimossa. Fallback su br-lan attivo."
```

Questo script agisce come **guardia di sicurezza**: anche se netifd/mwan3 inseriscono la rotta prima che il telefono sia pronto, lo script la rimuove entro ~6 secondi se i ping falliscono.

**Verifica log:**
```bash
docker exec homeassistant ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11 "logread | grep wan-verify"
```

### Architettura Routing OpenWrt (Riepilogo)

| Modalità | Rotta default primaria | Rotta fallback |
|---|---|---|
| **Normale** (Redmi OK) | `default via 10.x.x.x dev usb0 metric 10` | `default via 192.168.0.3 dev br-lan metric 30` |
| **Redmi offline/rotto** | *(rimossa da wan-verify)* | `default via 192.168.0.3 dev br-lan metric 30` ✅ |
| **Intranet (Debian)** | `default via 192.168.0.3 dev br-lan metric 30` | — |

### Diagnostica Rapida

```bash
# Stato mwan3
docker exec homeassistant ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11 "mwan3 status"

# Ping internet via usb0 (test diretto Redmi)
docker exec homeassistant ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11 "ping -c 2 -I usb0 8.8.8.8"

# Stato dati Android via ADB
docker exec homeassistant ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11 "adb_router shell dumpsys telephony.registry | grep mDataConnectionState"

# Rimozione emergenza rotta usb0 bloccante
docker exec homeassistant ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11 "while ip route del default dev usb0 2>/dev/null; do :; done; ip route show"

# Riattivazione manuale tethering
docker exec homeassistant ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11 "/usr/bin/enable_usb_tether.sh"
```

---
*Ultimo aggiornamento: 16 Agosto 2026*

#### 3. Configurazione Definitiva: Wi-Fi Attivo con IP Statico (Senza Gateway)

**Soluzione applicata e testata con successo (16/08/2026 14:35):**
Per mantenere sia il Wi-Fi che i Dati Mobili attivi sul Redmi 11 senza creare loop di routing, è stata applicata la **Soluzione A (IP Statico senza Gateway)** direttamente nelle impostazioni della rete Wi-Fi di casa (`CPE_2.4G_112E90`) sul telefono:

1. **Privacy Wi-Fi:** Impostato su *"Usa MAC dispositivo"* (MAC fisso `16:76:57:ba:d3:64`).
2. **Indirizzo IP Statico:** `192.168.0.14` (Netmask `/24`).
3. **Gateway:** `0.0.0.0` (oppure svuotato).
4. **DNS:** `192.168.0.3` (o `192.168.0.11`).

**Esito e Vantaggi:**
- **Traffico LAN:** Il Redmi resta connesso alla LAN di casa con IP `192.168.0.14` per tutte le comunicazioni locali.
- **Tethering USB / WAN:** Non avendo una rotta di default per internet sul Wi-Fi, Android assegna automaticamente ed al 100% il Tethering USB (`usb0`) alla rete dati mobile 4G/5G (**`rmnet_data1` / Tabella 1015**).
- **Prestazioni:** Latenza 19ms-22ms su `usb0`, 0% pacchetti persi.
- **Transizione HA:** Ripristino in modalità **Normale** completato con successo (`wan-verify OK`, `mwan3 online`, `Stato: idle / Modalità: server`).

---

## Fix Tethering USB Windows 11 via Impacket/atexec.py (19 Agosto 2026)

### Problema
L'esecuzione dello script PowerShell `usb_tether.ps1` su Windows 11 via SSH da Home Assistant falliva con **"Accesso negato"** su `New-NetNat` e `Set-NetIPInterface -Forwarding Enabled`, perché la connessione SSH forniva un token UAC filtrato (non elevato).

### Soluzione: Impacket `atexec.py` come SYSTEM
Installato `impacket` nel container Home Assistant e riscritto `usb_tether_ha.sh` per usare `atexec.py` (ATSVC over SMB/RPC) che esegue comandi come **NT AUTHORITY\SYSTEM**, bypassando UAC.

#### Componenti
| Componente | Descrizione |
|------------|-------------|
| **impacket** | `pip install impacket` nel container HA → fornisce `atexec.py` |
| **Password Windows** | Salvata in `/config/.secrets/win_pw` (chmod 600, montato via volume `./config:/config`) |
| **`run_atexec()` helper** | Legge password dal file, codifica comando PowerShell in Base64 UTF-16LE (`-EncodedCommand`), invoca `atexec.py "user:pass@host" "powershell.exe -EncodedCommand ..."` |
| **`usb_tether.ps1 -ViaScheduledTask`** | Flag per indicare esecuzione elevata: scrive risultato in `C:\Windows\Temp\usb_tether_result.json` (leggibile da ADMIN$) invece di stdout |

#### Funzioni riscritte in `usb_tether_ha.sh`
- **`activate_windows()`** → chiama `run_atexec` per `activate`, gestisce router cutover separatamente
- **`restore_windows()`** → solo parte router; il vero restore Windows è in `router_finish_restore_windows()` dopo drenaggio
- **`router_finish_restore_windows()`** → chiama `run_atexec` per `restore` (spegnimento NAT Windows) dopo conferma drenaggio router
- **`run_status()`** → usa `run_atexec` per `status` (legge `C:\ProgramData\usb_tether_state.json` che richiede admin), estrae JSON da output Impacket (rimuove BOM UTF-8 `\xEF\xBB\xBF`)

#### Configurazione HA
```yaml
# docker-compose.yml - environment per container homeassistant
services:
  homeassistant:
    environment:
      - IMPACKET_PW_FILE=/config/.secrets/win_pw
```

#### Test verifica
```bash
# Da HA container:
docker exec -e IMPACKET_PW_FILE=/config/.secrets/win_pw homeassistant \
  atexec.py "carlo_2:$(cat /config/.secrets/win_pw)@192.168.0.8" "whoami"
# Output atteso: nt authority\system
```

#### Risultato
- **Attivazione intranet**: NAT Windows creato, forwarding abilitato, router riceve route fallback `default via 192.168.0.8 metric 30`
- **Internet via router**: `ping 8.8.8.8` dal router OK (51-68ms)
- **Status HA**: Legge stato correttamente via `atexec.py`
- **Ripristino**: NAT Windows spento dopo drenaggio router confermato

#### Limitazione nota
Il **watchdog** (Scheduled Task `USBTetherWatchdog` per auto-restore) fallisce con errore SID quando registrato come SYSTEM. L'auto-restore post-scadenza va gestito manualmente o fixato separatamente.

---

*Ultimo aggiornamento: 19 Agosto 2026*

---
*Ultimo aggiornamento: 16 Agosto 2026*

## Watchdog Coordinato da Home Assistant (20 Agosto 2026)

### Problema
Il **watchdog Windows** basato su `Task Scheduler` (`USBTetherWatchdog`) eseguito come `NT AUTHORITY\SYSTEM` da `atexec.py` falliva con **`HRESULT 0x80070534`** ("Impossibile trovare il gruppo specificato") e non riusciva a registrarsi affidabilmente. A causa del suo malfunzionamento il ripristino post-scadenza non avveniva mai in automatico.

### Soluzione: spostamento del watchdog su Home Assistant
Il watchdog è stato **completamente rimosso** da `usb_tether.ps1` e l'intera logica di auto-ripristino coordinato ora risiede in **`helpers/usb_tether_ha.sh`** nel container HA. Lo script HA:

1. **Attende la scadenza** del timeout configurato (`input_number.usb_tether_max_duration`).
2. **Avvia `restore_windows`** che esegue la sequenza in ordine fallo:
   1. marca i flussi protetti sul router (`tethering-graceful.sh begin`);
   2. ripristina la WAN router (`usb0 metric 10`);
   3. rimuove la route fallback via Windows (`metric 30`);
   4. avvia il drenaggio in background.
3. **`router_finish_restore_windows()`** attende che il drenaggio conntrack del router sia completato (controlla la rimozione della regola `CONNMARK`), poi:
   1. spegne il NAT Windows via `atexec.py` come `SYSTEM`;
   2. pulisce la route fallback residua;
   3. flusha le entry conntrack del device protetto.

> Il **fail-closed** è garantito: le route del router non vengono mai modificate se Windows non conferma `active`.

#### Architettura watchdog HA (riassunto)
| Step | Responsabile | Azione |
|-------|-------------|--------|
| 1. Timeout scaduto | `usb_tether_ha.sh` | trigger `auto_restore_windows` (dopo `max_minutes * 60 - 25s`) |
| 2. Protezione flussi | Router OpenWrt | `tethering-graceful.sh begin` con MARK `0x89` |
| 3. WAN locale | `ssh_router` | ripristino route `usb0 metric 10` |
| 4. Rimozione fallback | `ssh_router` | rimozione `default via 192.168.0.8 metric 30` |
| 5. Drenaggio | Router OpenWrt | `tethering-graceful.sh end` (background) |
| 6. Attesa drenaggio | `usb_tether_ha.sh` | polling FINO a tetto 6h (`ROUTER_DRAIN_CEILING=21600`) |
| 7. Spegnimento NAT | `atexec.py` (SYSTEM) | `usb_tether.ps1 -Action restore` |
| 8. Pulizia | Router OpenWrt | `ip route del default via 192.168.0.8`, `conntrack -D` |

#### Verifica
```bash
# Processo watchdog HA in esecuzione
docker exec homeassistant sh -c 'ps -ef | grep "[u]sb_tether_ha.sh auto_restore_windows"'

# Stato corrente del watchdog (dovrebbe mostrare "restoring")
docker exec homeassistant /config/helpers/usb_tether_ha.sh status server auto 60

# Router instradato correttamente via Windows (route fallback attiva)
docker exec homeassistant ssh -i /config/.ssh/router_key -o BatchMode=yes root@192.168.0.11 "ip route show default"
```

---
*Ultimo aggiornamento: 20 Agosto 2026*



