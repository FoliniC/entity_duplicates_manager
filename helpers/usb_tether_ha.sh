#!/usr/bin/env bash
set -u

ACTION="${1:-status}"
MODE="${2:-server}"
HOST="${3:-Debian (192.168.0.3)}"
DURATION="${4:-60}"
IS_ROLLBACK="${5:-0}"

LOG_FILE="/config/logs/usb_tether/usb_tether.log"
RESTORE_MARKER="/config/logs/usb_tether/restoring_windows.marker"
SSH_CM_DIR="/config/.ssh/cm"
WINDOWS_GW="192.168.0.8"
# Fallback file per la password atexec.py se IMPACKET_PW non e' impostata
# nell'ambiente del container. chmod 600, proprietario = utente del container HA.
IMPACKET_PW_FILE="/config/.secrets/win_pw"
ROUTER_WAN_IF="usb0"
ROUTER_WAN_METRIC="10"
WINDOWS_ROUTE_METRIC="30"
# Costanti per graceful transition router
ROUTER_TABLE_LEAVE_WAN=87
ROUTER_MARK_LEAVE_WAN=0x87
ROUTER_TABLE_LEAVE_ANCHOR=89
ROUTER_MARK_LEAVE_ANCHOR=0x89
ROUTER_DRAIN_CEILING=21600
ROUTER_GRACEFUL_SCRIPT="/usr/bin/tethering-graceful.sh"
# IP riservato (DHCP statico) del device da proteggere in modo prioritario
# sul router, es. Echo. Vuoto = router_graceful_* diventano no-op sicuri.
PROTECTED_DEVICE_IP="192.168.0.90"

# NOTA: la vecchia tabella 88 (timer fisso 180s, CONNMARK scritto a mano)
# e' stata rimossa: restore_windows ora usa tethering-graceful.sh con
# ROUTER_TABLE_LEAVE_ANCHOR/MARK sopra, drenaggio su conntrack invece di un
# timer fisso. Se sul router e' rimasto stato residuo dalla vecchia tabella
# 88 (es. da test precedenti), ripulirlo manualmente una tantum:
#   ssh_router "iptables -t mangle -F PREROUTING 2>/dev/null; \
#     ip rule del pref 88 2>/dev/null; ip route flush table 88 2>/dev/null"
# (verificare prima con "iptables -t mangle -L PREROUTING" e "ip rule show"
# che non ci sia altro di legittimo su quella catena/tabella).

mkdir -p "$SSH_CM_DIR" /config/logs/usb_tether

# Error marker file for pre-flight check failures
ERROR_MARKER="/config/logs/usb_tether/last_error.marker"

log_line() {
  local level="$1"
  local msg="$2"
  msg="$(printf '%s' "$msg" | tr '\r\n' '  ')"
  printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$level" "$msg" >> "$LOG_FILE"
}

json_error() {
  local msg="$1"
  msg="${msg//\\/\\\\}"
  msg="${msg//\"/\\\"}"
  printf '{"state":"error","mode":"%s","message":"%s"}\n' "$MODE" "$msg"
}

ssh_windows() {
  ssh -i /config/.ssh/win_key \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=QUIET \
    -o ConnectTimeout=10 \
    -o ControlMaster=auto \
    -o ControlPersist=60s \
    -o ControlPath=/config/.ssh/cm/%C \
    carlo_2@192.168.0.8 "$@"
}

ssh_debian() {
  ssh -i /config/.ssh/ha_host_key \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=QUIET \
    -o ConnectTimeout=10 \
    -o ControlMaster=auto \
    -o ControlPersist=60s \
    -o ControlPath=/config/.ssh/cm/%C \
    -o IdentitiesOnly=yes \
    carlo@192.168.0.3 "$@"
}

ssh_router() {
  ssh -i /config/.ssh/router_key \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=QUIET \
    -o ConnectTimeout=5 \
    root@192.168.0.11 "$@"
}

schedule_self() {
  local action="$1"
  local delay="$2"
  # setsid, non nohup: nohup blocca solo SIGHUP, non stacca dal process
  # group. Se Home Assistant termina l'intero process group del comando
  # shell_command quando questo finisce (comportamento comune per evitare
  # processi orfani), un job in background con solo "nohup ... &" muore
  # insieme al padre prima ancora di eseguire il suo sleep. setsid crea una
  # nuova sessione, staccata da qualunque process group killing a monte.
  setsid "$0" "$action" "$delay" "$HOST" "$DURATION" >/dev/null 2>&1 < /dev/null &
}

# atexec.py esegue PowerShell senza una console interattiva. Write-Host e gli
# stream PowerShell vengono quindi serializzati in CLIXML, non emessi come una
# riga JSON nuda. Estraiamo il JSON dallo stream prima di prendere decisioni
# sul routing: il codice di uscita di atexec.py dice solo che il task remoto è
# partito, non che l'attivazione del NAT Windows sia riuscita.
extract_windows_json() {
  printf '%s\n' "$1" | tr -d '\r' \
    | grep -oE '\{[^{}]*"state"[[:space:]]*:[[:space:]]*"(active|error|idle|restoring)"[^{}]*\}' \
    | tail -1
}

# cmd_detect può emettere un warning ed uscire con codice 0 quando il telefono
# non c'è. Accettiamo solo il formato effettivo IFACE|IPv4, mai testo generico.
# L'alias di Windows può contenere spazi (ad esempio "Ethernet 2").
extract_phone_detection() {
  printf '%s\n' "$1" | tr -d '\r' \
    | grep -E '^.+\|([0-9]{1,3}\.){3}[0-9]{1,3}$' \
    | tail -1
}

run_status() {
  local out rc line

  # Check for error marker first
  if [[ -f "$ERROR_MARKER" ]]; then
    local err_msg err_time
    err_msg=$(head -1 "$ERROR_MARKER" 2>/dev/null)
    err_time=$(sed -n '2p' "$ERROR_MARKER" 2>/dev/null)
    if [[ -n "$err_msg" ]]; then
      # Before returning stale error, check if current status is actually working
      # If tethering is idle/active, clear the stale error marker and return real status
      if [[ "$HOST" == *"Windows"* ]]; then
        out=$(ssh_windows "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action status" 2>&1)
        rc=$?
        out=$(extract_windows_json "$out")
      else
        out="$(ssh_debian "/home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh status" 2>&1)"
        rc=$?
      fi
      if (( rc == 0 )); then
        line="$(printf '%s\n' "$out" | tr -d '\r' | awk '/^\{.*\}$/ { last=$0 } END { print last }')"
        if [[ -n "$line" ]] && [[ "$line" == *'"state":"active"'* ]]; then
          # Current status is active - clear stale error marker
          rm -f "$ERROR_MARKER" 2>/dev/null || true
          log_line INFO "Cleared stale error marker: current tethering state is active"
          printf '%s\n' "$line"
          return 0
        fi
      fi
      # Current status not healthy - return the error marker
      if [[ -n "$err_time" ]]; then
        printf '{"state":"error","mode":"%s","message":"%s (alle %s)"}\n' "$MODE" "$err_msg" "$err_time"
      else
        printf '{"state":"error","mode":"%s","message":"%s"}\n' "$MODE" "$err_msg"
      fi
      return 0
    fi
  fi

  # Se un restore (Debian o Windows) e' in corso, restituisce immediatamente 'restoring'
  if [[ -f "$RESTORE_MARKER" ]]; then
    printf '{"state":"restoring","mode":"server","message":"Ripristino routing normale in corso..."}\n'
    return 0
  fi

  # Il selettore HA torna al valore iniziale dopo alcuni riavvii; non deve
  # quindi poter nascondere un'intranet Windows già attiva. In modalità auto
  # Windows è la fonte prioritaria: se è active/restoring/error la riportiamo,
  # altrimenti interroghiamo Debian.
  if [[ "$HOST" == "auto" ]]; then
    local auto_out auto_rc auto_line
    # Lo stato è leggibile anche via OpenSSH non elevato e questo evita il
    # polling ATSVC/SMB di atexec.py, troppo lento per command_line (30s).
    auto_out=$(ssh_windows "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action status" 2>&1)
    auto_rc=$?
    auto_line=$(extract_windows_json "$auto_out")
    if (( auto_rc == 0 )) && [[ -n "$auto_line" ]] \
       && [[ "$auto_line" != *'"state":"idle"'* ]]; then
      printf '%s\n' "$auto_line"
      return 0
    fi
    HOST="Debian (192.168.0.3)"
  fi

  if [[ "$HOST" == *"Windows"* ]]; then
    # Status non richiede mutazioni privilegiate: SSH diretto è molto più
    # rapido e impedisce che il sensore command_line resti indietro.
    out=$(ssh_windows "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action status" 2>&1)
    rc=$?
    out=$(extract_windows_json "$out")
  else
    out="$(ssh_debian "/home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh status" 2>&1)"
    rc=$?
  fi

  if (( rc != 0 )); then
    json_error "status fallito rc=$rc: $out"
    return 0
  fi

  line="$(printf '%s\n' "$out" | tr -d '\r' | awk '/^\{.*\}$/ { last=$0 } END { print last }')"
  if [[ -n "$line" ]]; then
    printf '%s\n' "$line"
  else
    json_error "status senza JSON: $out"
  fi
}

# Helper: encode PowerShell command for atexec.py (Base64 UTF-16LE)
encode_ps_command() {
  local cmd="$1"
  echo -n "$cmd" | iconv -t UTF-16LE | base64 -w 0
}

# Helper: run command on Windows via atexec.py as SYSTEM (bypasses UAC)
# Usage: run_atexec "command string"
run_atexec() {
  local cmd="$1"
  local encoded
  encoded=$(encode_ps_command "$cmd")

  # Password: prima env var IMPACKET_PW (comodo per test manuali), altrimenti
  # file dedicato IMPACKET_PW_FILE (consigliato per l'uso da HA: non finisce
  # in chiaro in "docker inspect" o "systemctl show").
  local pw="${IMPACKET_PW:-}"
  if [[ -z "$pw" && -f "$IMPACKET_PW_FILE" ]]; then
    pw="$(cat "$IMPACKET_PW_FILE" 2>/dev/null)"
  fi

  if [[ -z "$pw" ]]; then
    log_line ERROR "run_atexec: nessuna password disponibile (ne' IMPACKET_PW ne' $IMPACKET_PW_FILE) - abort per evitare che atexec.py resti appeso in attesa di input"
    printf '{"state":"error","message":"credenziali atexec.py mancanti"}\n'
    return 1
  fi

  # NOTA: la password compare comunque per un istante negli argv di questo
  # processo (visibile via "ps auxww" ad altri processi locali) perche'
  # atexec.py la vuole nella stringa target. Su questa rete domestica e'
  # un rischio accettato; per eliminarlo del tutto servirebbe autenticazione
  # via -hashes (NTLM pass-the-hash) invece della password in chiaro.
  local target="carlo_2:${pw}@192.168.0.8"
  if command -v atexec.py >/dev/null 2>&1; then
    atexec.py "$target" "powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded" 2>&1
  else
    ssh_windows "powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded" 2>&1
  fi
}

activate_windows() {
  local out rc router_out router_rc result_json detect_line
  
  # PRE-FLIGHT CHECK: Verifica che il tethering USB sia disponibile su Windows
  local detect_out
  detect_out="$(ssh_windows "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action detect" 2>&1)"
  local detect_rc=$?
  detect_line=$(extract_phone_detection "$detect_out")
  if (( detect_rc != 0 )) || [[ -z "$detect_line" ]]; then
    log_line ERROR "PRE-FLIGHT FALLITO: Nessun tethering USB rilevato su Windows. Output: $detect_out"
    rm -f /config/.usb_tether_mode 2>/dev/null || true
    rm -f "$ERROR_MARKER" 2>/dev/null || true
    json_error "Tethering USB non disponibile su Windows: collega il telefono e attiva il tethering USB prima di procedere"
    return 0
  fi
  # Clear error marker on success
  rm -f "$ERROR_MARKER" 2>/dev/null || true
  log_line INFO "PRE-FLIGHT OK: Tethering USB rilevato su Windows -> $detect_line"
  
  # Salva la modalita' per router_check
  echo "$MODE" > /config/.usb_tether_mode 2>/dev/null || true

  # Avvia watchdog solo ORA che il preflight ha avuto successo
  if [ "$IS_ROLLBACK" != "1" ]; then
    nohup /config/helpers/failsafe_watchdog.sh "normale" "$HOST" 60 >/dev/null 2>&1 &
  fi

  # Pulizia di sicurezza: un marker rimasto da un restore precedente
  # interrotto bloccherebbe run_status su "restoring" per sempre.
  rm -f "$RESTORE_MARKER" 2>/dev/null || true

  # --- USA ATEXEC.PY COME SYSTEM (bypassa UAC, non serve Task Scheduler) ---
  local ps_cmd="C:/Scripts/usb_tether.ps1 -Action activate -MaxMinutes $DURATION -Mode $MODE -ViaScheduledTask"
  
  log_line INFO "EXEC Windows activate $MODE via atexec.py (SYSTEM)..."
  out=$(run_atexec "$ps_cmd")
  rc=$?
  log_line INFO "EXEC Windows activate $MODE rc=$rc | $(printf '%s' "$out" | tail -c 500)"
  
  # atexec.py ritorna output diretto, niente polling file necessario
  # Controlla se l'output contiene JSON di errore
  result_json=$(extract_windows_json "$out")

  if (( rc != 0 )); then
    log_line ERROR "Attivazione Windows via atexec.py fallita rc=$rc"
    json_error "attivazione Windows fallita rc=$rc"
    return 0
  elif [[ -z "$result_json" ]]; then
    # Non modificare MAI le route del router senza una conferma esplicita che
    # Windows abbia creato il NAT. In precedenza questo ramo proseguiva e
    # rimuoveva usb0 anche dopo un errore del task remoto, isolando la LAN.
    log_line ERROR "atexec.py non ha restituito uno stato Windows verificabile"
    json_error "attivazione Windows non verificabile: route router non modificata"
    return 0
  elif [[ "$result_json" == *'"state":"error"'* ]]; then
    log_line ERROR "Attivazione Windows fallita: $result_json"
    local msg
    msg=$(echo "$result_json" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p')
    json_error "${msg:-Attivazione Windows fallita}"
    return 0
  elif [[ "$result_json" != *'"state":"active"'* ]]; then
    log_line ERROR "Attivazione Windows non confermata: $result_json"
    json_error "attivazione Windows non confermata: route router non modificata"
    return 0
  else
    log_line INFO "Attivazione Windows confermata: $result_json"
  fi

  if [[ "$MODE" == "intranet" ]]; then
    # 1. Prende il gateway WAN REALE da ifstatus (non dal default route corrente,
    #    che potrebbe già puntare a Windows se siamo in transizione)
    local cur_gw
    cur_gw=$(ssh_router "ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1" 2>&1 | tr -d '\r')
    if [[ ! "$cur_gw" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      log_line ERROR "Impossibile determinare gateway WAN attuale su $ROUTER_WAN_IF"
      json_error "router via Windows fallito: gateway WAN non trovato"
      return 0
    fi

    # 2. Protegge SUBITO i flussi che stanno usando la WAN locale (usb0)
    #    Prima di aggiungere la route fallback via Windows, marca i flussi
    #    ESTABLISHED/RELATED del device protetto e li dirotta via tabella dedicata.
    router_out="$(ssh_router "$ROUTER_GRACEFUL_SCRIPT begin $ROUTER_TABLE_LEAVE_WAN $ROUTER_MARK_LEAVE_WAN $PROTECTED_DEVICE_IP $cur_gw $ROUTER_WAN_IF" 2>&1)"
    router_rc=$?
    log_line INFO "EXEC Router graceful begin leave-WAN rc=$router_rc | $(printf '%s' "$router_out" | tail -c 500)"
    if (( router_rc != 0 )); then
      json_error "router graceful begin leave-WAN fallito rc=$router_rc"
      return 0
    fi

    # 3. Aggiunge la route fallback via Windows (metric 30)
    router_out="$(ssh_router "ip route replace default via $WINDOWS_GW dev br-lan metric $WINDOWS_ROUTE_METRIC; ip route show default; true" 2>&1)"
    router_rc=$?
    log_line INFO "EXEC Router prepare Windows rc=$router_rc | $(printf '%s' "$router_out" | tail -c 500)"
    if (( router_rc != 0 )); then
      json_error "router via Windows fallito rc=$router_rc"
      return 0
    fi
    log_line INFO "TRANSIZIONE Windows intranet: WAN router $ROUTER_WAN_IF mantenuta (protezione flussi attiva), poi cutover graceful via $WINDOWS_GW"
    schedule_self router_cutover_windows 2
  fi

  # Il Task Scheduler Windows eseguito da atexec/SYSTEM non può coordinare il
  # ripristino delle route OpenWrt e in alcune installazioni non si registra
  # affatto (HRESULT 0x80070534). Il watchdog deve quindi restare qui, dove
  # può ripristinare router e NAT nell'ordine corretto.
  schedule_self auto_restore_windows "$((DURATION * 60))"

  printf '{"state":"activating","mode":"%s","message":"Attivazione in corso..."}\n' "$MODE"
}

activate_debian() {
  local out rc

  # PRE-FLIGHT CHECK: Verifica che il tethering USB sia disponibile su Debian
  # Riprova fino a 3s per consentire al sistema di stabilizzare carrier e DHCP se appena collegato
  local detect_out="" detect_rc=1
  for attempt in $(seq 1 3); do
    detect_out="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh detect" 2>&1)"
    detect_rc=$?
    if (( detect_rc == 0 )) && [[ -n "$detect_out" ]]; then
      break
    fi
    sleep 1
  done

  if (( detect_rc != 0 )) || [[ -z "$detect_out" ]]; then
    log_line ERROR "PRE-FLIGHT FALLITO: Nessun tethering USB rilevato su Debian dopo 3s. Output: $detect_out"
    # Interrompi eventuale watchdog per evitare falsi positivi
    pkill -f failsafe_watchdog.sh >/dev/null 2>&1 || true
    rm -f /config/.usb_tether_mode 2>/dev/null || true
    rm -f "$ERROR_MARKER" 2>/dev/null || true
    json_error "Tethering USB non disponibile su Debian: collega il telefono e attiva il tethering USB prima di procedere"
    return 0
  fi

  # Parse IFACE|GW from detect output
  local detect_iface detect_gw
  detect_iface=$(echo "$detect_out" | cut -d'|' -f1)
  detect_gw=$(echo "$detect_out" | cut -d'|' -f2)

  # PRE-FLIGHT INTERNET: prima rende la USB il default upstream di Debian,
  # poi verifica connettività REALE vincolata all'interfaccia.
  # Questo è necessario per Intranet: una connessione NM con never-default=yes
  # ha lease e gateway ma non può instradare la LAN via NAT.
  if [[ "$MODE" == "intranet" ]]; then
    local route_setup
    route_setup="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh ensure_usb_default $detect_iface" 2>&1)"
    if [[ $? -ne 0 ]]; then
      log_line ERROR "PRE-FLIGHT FALLITO: impossibile configurare $detect_iface come upstream USB Debian: $route_setup"
      pkill -f failsafe_watchdog.sh >/dev/null 2>&1 || true
      rm -f /config/.usb_tether_mode 2>/dev/null || true
      json_error "Impossibile preparare il routing USB Debian su $detect_iface"
      return 0
    fi
    detect_gw=$(printf '%s' "$route_setup" | tail -1 | cut -d'|' -f2)
    log_line INFO "PRE-FLIGHT ROUTING: $detect_iface configurata come default upstream Debian (GW=$detect_gw)"
  fi

  log_line INFO "PRE-FLIGHT INTERNET: verifica connettività via $detect_iface (GW=$detect_gw)..."
  local inet_test
  inet_test="$(ssh_debian "ping -c 2 -W 3 -I $detect_iface 8.8.8.8 >/dev/null 2>&1 || ping -c 2 -W 3 -I $detect_iface 1.1.1.1 >/dev/null 2>&1; echo \$?" 2>&1)"
  if [[ "$inet_test" != "0" ]]; then
    log_line ERROR "PRE-FLIGHT FALLITO: Internet non raggiungibile via $detect_iface (GW=$detect_gw). Tethering attivo ma NAT mobile non instrada verso internet."
    pkill -f failsafe_watchdog.sh >/dev/null 2>&1 || true
    rm -f /config/.usb_tether_mode 2>/dev/null || true
    rm -f "$ERROR_MARKER" 2>/dev/null || true
    json_error "Internet non raggiungibile via $detect_iface (GW=$detect_gw): tethering USB attivo ma NAT mobile non instrada verso internet"
    return 0
  fi
  log_line INFO "PRE-FLIGHT OK: Internet raggiungibile via $detect_iface (GW=$detect_gw)"

  # Clear error marker on success
  rm -f "$ERROR_MARKER" 2>/dev/null || true
  rm -f "$RESTORE_MARKER" 2>/dev/null || true

  log_line INFO "PRE-FLIGHT OK: Tethering USB rilevato su Debian -> $detect_out"

  # Salva la modalita' per router_check
  echo "$MODE" > /config/.usb_tether_mode 2>/dev/null || true

  # Avvia watchdog solo ORA che il preflight ha avuto successo
  if [ "$IS_ROLLBACK" != "1" ]; then
    nohup /config/helpers/failsafe_watchdog.sh "normale" "$HOST" 60 >/dev/null 2>&1 &
  fi

  if [[ "$MODE" == "intranet" ]]; then
    out="$(ssh_debian "nohup setsid sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh activate $DURATION intranet >/dev/null 2>&1 &" 2>&1)"
  else
    out="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh activate $DURATION server" 2>&1)"
  fi
  rc=$?
  log_line INFO "EXEC Debian activate $MODE rc=$rc | $(printf '%s' "$out" | tail -c 500)"
  if (( rc != 0 )); then
    pkill -f failsafe_watchdog.sh >/dev/null 2>&1 || true
    json_error "activate Debian fallito rc=$rc"
    return 0
  fi
  printf '{"state":"activating","mode":"%s","message":"Attivazione in corso..."}\n' "$MODE"
  return 0
}

restore_windows() {
  local out rc router_out router_rc

  # 1. Protegge SUBITO (prima di toccare qualunque route) i flussi del
  #    device protetto che stanno ancora usando l'anchor Windows - stessa
  #    tabella/mark dedicati usati per l'altra direzione (87 vs 89), stesso
  #    script tethering-graceful.sh invece della logica scritta a mano che
  #    c'era qui prima (tabella 88, timer fisso 180s).
  router_out="$(ssh_router "$ROUTER_GRACEFUL_SCRIPT begin $ROUTER_TABLE_LEAVE_ANCHOR $ROUTER_MARK_LEAVE_ANCHOR $PROTECTED_DEVICE_IP $WINDOWS_GW br-lan" 2>&1)"
  router_rc=$?
  log_line INFO "EXEC Router graceful begin leave-anchor rc=$router_rc | $(printf '%s' "$router_out" | tail -c 500)"
  if (( router_rc != 0 )); then
    json_error "router graceful begin leave-anchor fallito rc=$router_rc"
    return 0
  fi

  # 2. Ripristina la WAN locale del router (route vera, non solo stato netifd).
  router_out="$(ssh_router "
    GW=\$(ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1);
    if [ -n \"\$GW\" ]; then
      ip route replace default via \"\$GW\" dev $ROUTER_WAN_IF metric $ROUTER_WAN_METRIC 2>/dev/null;
    else
      ifup wan >/dev/null 2>&1;
      sleep 2;
      GW=\$(ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1);
      [ -n \"\$GW\" ] && ip route replace default via \"\$GW\" dev $ROUTER_WAN_IF metric $ROUTER_WAN_METRIC 2>/dev/null;
    fi;
    echo ROUTES; ip route show default; true
  " 2>&1)"
  router_rc=$?
  log_line INFO "EXEC Router restore WAN rc=$router_rc | $(printf '%s' "$router_out" | tail -c 500)"

  # 3. Rimuovi SUBITO la route fallback via Windows da main: le nuove
  #    connessioni vedono solo la WAN locale. Quelle marcate restano
  #    protette dalla tabella dedicata (fwmark, gia' attiva dal punto 1).
  router_out="$(ssh_router "ip route del default via $WINDOWS_GW dev br-lan metric $WINDOWS_ROUTE_METRIC 2>/dev/null; true" 2>&1)"
  router_rc=$?
  log_line INFO "EXEC Router remove Windows fallback route rc=$router_rc | $(printf '%s' "$router_out" | tail -c 300)"

  # 4. Avvia il drenaggio in background sul router (basato su conntrack, non
  #    a tempo fisso: uno stream continuo non "finisce" mai entro nessun
  #    timer, quindi un timer fisso lo interrompe comunque, prima o poi).
  router_out="$(ssh_router "$ROUTER_GRACEFUL_SCRIPT end $ROUTER_TABLE_LEAVE_ANCHOR $ROUTER_MARK_LEAVE_ANCHOR $ROUTER_DRAIN_CEILING" 2>&1)"
  router_rc=$?
  log_line INFO "EXEC Router graceful end leave-anchor (drain avviato) rc=$router_rc | $(printf '%s' "$router_out" | tail -c 300)"

  log_line INFO "TRANSIZIONE restore Windows: flussi esistenti protetti su tabella $ROUTER_TABLE_LEAVE_ANCHOR finche' non finiscono davvero (o scade il tetto), NAT Windows spento solo a drenaggio confermato"

  # Segna che un restore Windows e' in attesa del drenaggio: run_status lo
  # legge per riportare "restoring" invece di lasciar credere che sia bloccato.
  touch "$RESTORE_MARKER" 2>/dev/null || true

  # 5. Il NAT Windows va spento SOLO quando il router conferma che il
  #    drenaggio e' davvero finito: se lo spegnessimo prima, i flussi ancora
  #    instradati verso Windows via tabella dedicata resterebbero senza NAT
  #    a valle e si romperebbero comunque (il problema originale, spostato
  #    di un passo invece che risolto).
  # USA ATEXEC.PY COME SYSTEM per il restore Windows (dopo drenaggio router)
  # Nota: questo viene chiamato da router_finish_restore_windows dopo il drenaggio
  # Il job separato attende il drenaggio conntrack e poi spegne il NAT Windows.
  schedule_self router_finish_restore_windows 0

  printf '{"state":"restoring","mode":"server","message":"Ripristino in corso..."}\n'
}

auto_restore_windows() {
  local delay="${MODE:-0}"
  case "$delay" in ''|*[!0-9]*) delay=0 ;; esac
  sleep "$delay"
  log_line INFO "WATCHDOG HA: durata Windows scaduta, avvio restore coordinato"
  restore_windows >/dev/null 2>&1 || log_line ERROR "WATCHDOG HA: restore Windows fallito"
}

router_cutover_windows() {
  # Attende che la route fallback sia attiva e stabile (default 2s, configurabile)
  local delay="${MODE:-2}"
  case "$delay" in ''|*[!0-9]*) delay=2 ;; esac
  sleep "$delay"

  local out rc
  # Rimuove ORA la route WAN locale (usb0): senza questo passaggio 'main'
  # continuerebbe a preferirla per sempre (metric 10 < 30), e il cutover
  # verso Windows non si completerebbe mai per le connessioni nuove -
  # indipendentemente da quanto bene funzioni il drenaggio qui sotto.
  out="$(ssh_router "while ip route del default dev $ROUTER_WAN_IF metric $ROUTER_WAN_METRIC 2>/dev/null; do :; done; ip route show default; true" 2>&1)"
  rc=$?
  log_line INFO "EXEC Router remove local WAN route rc=$rc | $(printf '%s' "$out" | tail -c 300)"

  # Cutover graceful: avvia il drenaggio dei flussi marcati via tabella
  # dedicata (ROUTER_TABLE_LEAVE_WAN, mark ROUTER_MARK_LEAVE_WAN). Il
  # drenaggio attende che i flussi marcati finiscano davvero (conntrack)
  # o scade il tetto di sicurezza (ROUTER_DRAIN_CEILING).
  out="$(ssh_router "$ROUTER_GRACEFUL_SCRIPT end $ROUTER_TABLE_LEAVE_WAN $ROUTER_MARK_LEAVE_WAN $ROUTER_DRAIN_CEILING" 2>&1)"
  rc=$?
  log_line INFO "EXEC Router graceful cutover Windows (drain avviato) rc=$rc | $(printf '%s' "$out" | tail -c 500)"
}

router_finish_restore_windows() {
  local waited=0 max_wait="$ROUTER_DRAIN_CEILING" still_active="1" out rc router_out router_rc

  # Aspetta che il drenaggio sul router sia DAVVERO finito (tethering-graceful.sh
  # end gira in background li') prima di confermare: finche' il router instrada
  # ancora flussi marcati verso Windows via tabella dedicata, quei flussi hanno
  # bisogno del NAT Windows per uscire su internet - spegnerlo prima li romperebbe
  # comunque.
  while [ "$waited" -lt "$max_wait" ]; do
    # La chain resta creata anche dopo il drain; verificarne solo l'esistenza
    # farebbe attendere sempre il tetto di 6 ore. Il drain è concluso quando
    # non resta più la regola CONNMARK che instrada i flussi protetti.
    still_active="$(ssh_router "iptables -t mangle -S TETHER_${ROUTER_MARK_LEAVE_ANCHOR} 2>/dev/null | grep -q -- '-j CONNMARK' && echo 1 || echo 0" 2>/dev/null | tr -d '\r' | tail -1)"
    [ "$still_active" = "0" ] && break
    sleep 20
    waited=$((waited + 20))
  done
  log_line INFO "Router drenaggio leave-anchor confermato dopo ${waited}s (still_active=$still_active)"

  # 6. ORA spegni il NAT Windows via atexec.py (SYSTEM) - il router ha confermato
  #    che i flussi marcati sono finiti, quindi è sicuro disabilitare NAT Windows
  local ps_cmd="C:/Scripts/usb_tether.ps1 -Action restore -ViaScheduledTask"
  log_line INFO "EXEC Windows restore via atexec.py (SYSTEM)..."
  out=$(run_atexec "$ps_cmd")
  rc=$?
  log_line INFO "EXEC Windows restore rc=$rc | $(printf '%s' "$out" | tail -c 500)"

  # Pulizia finale: tabella/rule/chain le ha gia' tolte tethering-graceful.sh
  # end quando ha confermato il drenaggio; qui resta solo l'eventuale route
  # fallback via Windows, gia' rimossa al punto 3 di restore_windows ma
  # ripetuta qui per idempotenza (no-op se gia' assente).
  router_out="$(ssh_router "ip route del default via $WINDOWS_GW dev br-lan metric $WINDOWS_ROUTE_METRIC 2>/dev/null; ip route show default; true" 2>&1)"
  router_rc=$?
  log_line INFO "EXEC Router delayed cleanup Windows route rc=$router_rc | $(printf '%s' "$router_out" | tail -c 500)"

  # Rete di sicurezza per il caso limite (tetto raggiunto invece di drenaggio
  # pulito): forza la rinegoziazione di eventuali entry conntrack rimaste
  # appese su un path ormai morto.
  if [[ -n "$PROTECTED_DEVICE_IP" ]]; then
    local ct_out ct_rc
    ct_out="$(ssh_router "conntrack -D -s $PROTECTED_DEVICE_IP 2>/dev/null; conntrack -D -d $PROTECTED_DEVICE_IP 2>/dev/null; echo 'conntrack flush done'" 2>&1)"
    ct_rc=$?
    log_line INFO "EXEC Router conntrack flush $PROTECTED_DEVICE_IP rc=$ct_rc | $(printf '%s' "$ct_out" | tail -c 200)"
  fi

  rm -f "$RESTORE_MARKER" 2>/dev/null || true
}

restore_debian() {
  local out rc
  touch "$RESTORE_MARKER" 2>/dev/null || true

  # PRE-FLIGHT: verifica USB tethering prima di attivare "Normale".
  # Se assente (telefono non collegato o tethering spento), blocca e logga.
  log_line INFO "PRE-FLIGHT (normale): avvio preflight /config/helpers/usb_tether_preflight.sh"
  local pf_out pf_rc
  pf_out=$(bash /config/helpers/usb_tether_preflight.sh 2>&1)
  pf_rc=$?
  if [ "$pf_rc" -ne 0 ]; then
    log_line ERROR "PRE-FLIGHT FALLITO per normale: $pf_out"
    printf '%s\n%s\n' "USB tethering assente per normale: usb0 non rilevato" "$(date '+%Y-%m-%d %H:%M:%S')" > "$ERROR_MARKER"
    printf '{"state":"error","mode":"server","message":"Preflight normale fallito: USB tethering non disponibile"}\n'
    rm -f "$RESTORE_MARKER" 2>/dev/null || true
    return 0
  fi
  log_line INFO "PRE-FLIGHT OK per normale: $pf_out"
  rm -f "$ERROR_MARKER" 2>/dev/null || true

  # Esegue il restore Debian in FOREGROUND: il comando puo' impiegare ~47s
  # (ifup wan, graceful drain, conntrack flush sul router). Se restasse in
  # background, il processo muore quando HA reaps la shell_command, lasciando
  # lo STATE_FILE su Debian NON rimosso e il sensore bloccato in Intranet
  # (root cause del bug "Normale" che non puliva lo stato). La shell_command
  # ha command_timeout 120s, quindi il restore completa e rimuove lo stato.
  out=$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh restore" 2>&1)
  rc=$?
  log_line INFO "EXEC Debian restore completato rc=$rc | $(printf '%s' "$out" | tail -c 300)"
  rm -f "$RESTORE_MARKER" 2>/dev/null || true
  if [ "$rc" -eq 0 ]; then
    printf '{"state":"idle","mode":"server","message":"Ripristino completato"}\n'
  else
    printf '{"state":"error","mode":"server","message":"Errore restore (rc=%s): %s"}\n' "$rc" "$(printf '%s' "$out" | tail -c 200)"
  fi
}

run_router_check() {
  # Diagnostica la rotta primaria del router e verifica che l'Internet
  # sia effettivamente raggiungibile ATTRAVERSO la rotta attiva.
  #
  # Problema che rileva: in modalita intranet, se la route WAN (usb0, metric 10)
  # resta prioritaria sulla fallback Debian (br-lan, metric 30), la LAN perde
  # Internet anche se il tethering Debian e' attivo. Il ping da HA (Debian)
  # non vede il problema perche' parte da Debian stessa.
  #
  # Restituisce JSON:
  #   {"router_primary_route": "192.168.0.3 dev br-lan metric 30",
  #    "router_internet": "ok|dead",
  #    "router_ping_ms": 35.2,
  #    "wan_down_expected": true|false,
  #    "problem": ""|"wan_route_priority_intranet"}
  local primary_route ping_out ping_ms router_internet problem wan_down_expected

  primary_route=$(ssh_router "ip route show default 2>/dev/null" | sort -t' ' -k5 -n | head -1)
  if [[ -z "$primary_route" ]]; then
    primary_route="NESSUNA"
    router_internet="dead"
    ping_ms=0
    problem="no_default_route"
  else
    # Ping con retry: un singolo calo transitorio del bearer LTE (es. cambio
    # cella, scarso segnale) NON deve essere segnalato come "isolato". Ritenta
    # una seconda volta prima di dichiarare dead, per evitare falsi allarmi.
    local ping_ok=false
    ping_out=$(ssh_router "ping -c 3 -W 3 8.8.8.8 2>&1" | tail -2)
    if echo "$ping_out" | grep -qE " 0% packet loss"; then
      ping_ok=true
    else
      sleep 2
      ping_out=$(ssh_router "ping -c 3 -W 3 8.8.8.8 2>&1" | tail -2)
      if echo "$ping_out" | grep -qE " 0% packet loss"; then
        ping_ok=true
      fi
    fi
    if $ping_ok; then
      router_internet="ok"
      ping_ms=$(echo "$ping_out" | grep -oE "min/avg/max = [0-9.]+/[0-9.]+/[0-9.]+" | grep -oE "[0-9.]+/[0-9.]+/[0-9.]+" | cut -d/ -f2)
      ping_ms=${ping_ms:-0}
      problem=""
    else
      router_internet="dead"
      ping_ms=0
      problem="primary_route_no_internet"
    fi
  fi

  # In intranet la WAN (usb0) NON deve essere la rotta primaria.
  # Ma in modalita' Normale/Server, usb0 primaria e' CORRETTO (il telefono e'
  # fisicamente sul router). Quindi il bug si segnala SOLO se siamo in intranet.
  # Lo stato intranet lo leggiamo dal sensore HA via file di stato locale.
  local mode_active=""
  if [[ -f /config/.usb_tether_mode ]]; then
    mode_active=$(cat /config/.usb_tether_mode 2>/dev/null)
  fi
  if [[ "$primary_route" == *"usb0"* ]]; then
    wan_down_expected=false
    if [[ "$mode_active" == "intranet" ]]; then
      # Bug: in intranet il router non deve usare la WAN (il telefono e' sull'host)
      # L'anchor intranet e' a metric 9 (inferiore a usb0 metric 10), quindi se
      # usb0 resta la rotta primaria (metric 10) la LAN e' su un upstream morto.
      # Segnaliamo il bug SOLO se la WAN e' effettivamente morta (no internet):
      # se ha internet, non e' un problema reale anche se il file di modo e' fuori sincrono.
      if [[ "$primary_route" == *"metric 10"* ]] && [[ "$router_internet" == "dead" ]]; then
        problem="wan_route_priority_intranet"
      fi
    fi
  else
    wan_down_expected=true
  fi

  # Connessione effettiva (misurata sulla default route reale del router, non
  # sui flag dello script): dice QUALI device stanno realmente instradando.
  #   usb0                  -> Normale: tethering USB del Note 11 sul router (WAN)
  #   192.168.0.3 dev br-lan -> Intranet: telefono su Debian (Note 13/Pro 5G)
  #   NESSUNA               -> Isolata (nessun upstream attivo)
  local connection_reality
  if [[ "$primary_route" == *"usb0"* ]]; then
    connection_reality="Normale: tethering USB Note 11 (WAN router)"
  elif [[ "$primary_route" == *"192.168.0.3"* ]]; then
    connection_reality="Intranet: telefono su Debian (Note 13/Pro 5G)"
  elif [[ "$primary_route" == "NESSUNA" ]]; then
    connection_reality="Isolata: nessun upstream attivo"
  else
    connection_reality="Sconosciuta: $primary_route"
  fi

  printf '{"router_primary_route":"%s","router_internet":"%s","router_ping_ms":%s,"wan_down_expected":%s,"problem":"%s","connection_reality":"%s"}\n' \
    "$primary_route" "$router_internet" "$ping_ms" "$wan_down_expected" "$problem" "$connection_reality"
}

case "$ACTION" in
  status)
    run_status
    ;;
  router_check)
    run_router_check
    ;;
  router_cutover_windows)
    router_cutover_windows
    ;;
  router_finish_restore_windows)
    router_finish_restore_windows
    ;;
  auto_restore_windows)
    auto_restore_windows
    ;;
  reset)
    log_line INFO "[USER_ACTION] 🔴 RESET DI EMERGENZA PREMUTO: Interruzione watchdog in corso e ripristino forzato rete normale."
    pkill -f failsafe_watchdog.sh >/dev/null 2>&1 || true
    rm -f /config/logs/usb_tether/*.marker /config/logs/usb_tether/restoring_windows.marker >/dev/null 2>&1 || true
    if [[ "$HOST" == *"Windows"* ]]; then
      restore_windows
    else
      restore_debian
    fi
    ;;
  activate)
    # Pulizia preventiva: marker stale da restore precedenti bloccano run_status
    rm -f "$RESTORE_MARKER" 2>/dev/null || true
    pkill -f failsafe_watchdog.sh >/dev/null 2>&1 || true
    if [ "$IS_ROLLBACK" = "1" ]; then
      log_line INFO "[FAILSAFE_ROLLBACK] Esecuzione rollback automatico verso modalita $MODE (host: $HOST)"
    else
      log_line INFO "[USER_ACTION] PREMUTO BOTTONE: Attivazione modalita $MODE (host: $HOST, max_durata: ${DURATION}m)"
    fi
    if [[ "$HOST" == *"Windows"* ]]; then
      activate_windows
    else
      activate_debian
    fi
    ;;
  restore)
    if [ "$IS_ROLLBACK" = "1" ]; then
      log_line INFO "[FAILSAFE_ROLLBACK] Esecuzione rollback automatico verso modalita NORMALE (host: $HOST)"
    else
      pkill -f failsafe_watchdog.sh >/dev/null 2>&1 || true
      log_line INFO "[USER_ACTION] PREMUTO BOTTONE: Ripristino modalita NORMALE (host: $HOST, max_durata: ${DURATION}m)"
      nohup /config/helpers/failsafe_watchdog.sh "intranet" "$HOST" 45 >/dev/null 2>&1 &
    fi
    # Modalita' tornata normale: rimuovi il file di stato per router_check.
    rm -f /config/.usb_tether_mode 2>/dev/null || true
    if [[ "$HOST" == *"Windows"* ]]; then
      restore_windows
    else
      restore_debian
    fi
    ;;
  *)
    json_error "azione non valida: $ACTION"
    ;;
esac
