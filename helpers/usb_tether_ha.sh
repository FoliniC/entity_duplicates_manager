#!/usr/bin/env bash
set -u

ACTION="${1:-status}"
MODE="${2:-server}"
HOST="${3:-Debian (192.168.0.3)}"
DURATION="${4:-60}"

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
  ssh -i /config/.ssh/host_key \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o LogLevel=QUIET \
    -o ConnectTimeout=10 \
    -o ControlMaster=auto \
    -o ControlPersist=60s \
    -o ControlPath=/config/.ssh/cm/%C \
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

run_status() {
  local out rc line

  # Check for pre-flight error marker first
  if [[ -f "$ERROR_MARKER" ]]; then
    local err_msg err_time
    err_msg=$(head -1 "$ERROR_MARKER" 2>/dev/null)
    err_time=$(sed -n '2p' "$ERROR_MARKER" 2>/dev/null)
    if [[ -n "$err_msg" ]]; then
      printf '{"state":"error","mode":"%s","message":"%s (pre-flight fallito alle %s)"}\n' "$MODE" "$err_msg" "$err_time"
      return 0
    fi
  fi

  # Se un restore Windows e' in attesa del drenaggio router (puo' durare
  # minuti, anche ore), Windows non ha ancora richiamato il proprio
  # -Action restore: il suo stato locale direbbe ancora "active", che
  # sembrerebbe un blocco invece di un ripristino graduale in corso.
  if [[ "$HOST" == *"Windows"* ]] && [[ -f "$RESTORE_MARKER" ]]; then
    printf '{"state":"restoring","mode":"server","message":"Ripristino in corso (drenaggio flussi protetti sul router)..."}\n'
    return 0
  fi

  if [[ "$HOST" == *"Windows"* ]]; then
    # Usa atexec.py per leggere lo stato (richiede elevazione per leggere C:\ProgramData\usb_tether_state.json)
    local ps_cmd="C:/Scripts/usb_tether.ps1 -Action status -ViaScheduledTask"
    out=$(run_atexec "$ps_cmd")
    rc=$?
    
    # run_atexec output include log Impacket + JSON (con possibile BOM UTF-8: \xEF\xBB\xBF).
    # Estrae l'ultima occorrenza di JSON valido con campo "state" (ignorando BOM e log).
    # Usa sed per rimuovere BOM, poi grep per JSON con "state"
    out=$(printf '%s\n' "$out" | sed 's/\xEF\xBB\xBF//g' | grep -E '\{.*"state"\s*:\s*"(active|error|idle|restoring)"' | tail -1)
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
  atexec.py "$target" "powershell.exe -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded" 2>&1
}

activate_windows() {
  local out rc router_out router_rc
  
  # PRE-FLIGHT CHECK: Verifica che il tethering USB sia disponibile su Windows
  local detect_out
  detect_out="$(ssh_windows "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action detect" 2>&1)"
  local detect_rc=$?
  if (( detect_rc != 0 )) || [[ -z "$detect_out" ]]; then
    log_line ERROR "PRE-FLIGHT FALLITO: Nessun tethering USB rilevato su Windows. Output: $detect_out"
    # Write error marker for sensor to pick up
    printf '%s\n%s\n' "Tethering USB non disponibile su Windows: collega il telefono e attiva il tethering USB prima di procedere" "$(date '+%Y-%m-%d %H:%M:%S')" > "$ERROR_MARKER"
    json_error "Tethering USB non disponibile su Windows: collega il telefono e attiva il tethering USB prima di procedere"
    return 0
  fi
  # Clear error marker on success
  rm -f "$ERROR_MARKER" 2>/dev/null || true
  log_line INFO "PRE-FLIGHT OK: Tethering USB rilevato su Windows -> $detect_out"
  
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
  local result_json
  result_json=$(printf '%s\n' "$out" | grep -E '^\s*\{.*"state"\s*:\s*"(active|error)"' | tail -1)
  
  if [[ -n "$result_json" && "$result_json" == *"error"* ]]; then
    log_line ERROR "Attivazione Windows fallita: $result_json"
    local msg
    msg=$(echo "$result_json" | sed -n 's/.*"message":"\([^"]*\)".*/\1/p')
    json_error "${msg:-Attivazione Windows fallita}"
    return 0
  elif [[ -z "$result_json" ]]; then
    # Fallback: se atexec non ha restituito JSON parsabile, logga e procedi
    log_line WARN "atexec.py output non contiene JSON stato atteso: $out"
    # Non bloccare - il router side potrebbe aver funzionato
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

  printf '{"state":"activating","mode":"%s","message":"Attivazione in corso..."}\n' "$MODE"
}

activate_debian() {
  local out rc
  
  # PRE-FLIGHT CHECK: Verifica che il tethering USB sia disponibile su Debian
  # Prima di tentare l'attivazione (specialmente per intranet che gira in background)
  local detect_out
  detect_out="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh detect" 2>&1)"
  local detect_rc=$?
  if (( detect_rc != 0 )) || [[ -z "$detect_out" ]]; then
    log_line ERROR "PRE-FLIGHT FALLITO: Nessun tethering USB rilevato su Debian. Output: $detect_out"
    # Write error marker for sensor to pick up
    printf '%s\n%s\n' "Tethering USB non disponibile su Debian: collega il telefono e attiva il tethering USB prima di procedere" "$(date '+%Y-%m-%d %H:%M:%S')" > "$ERROR_MARKER"
    json_error "Tethering USB non disponibile su Debian: collega il telefono e attiva il tethering USB prima di procedere"
    return 0
  fi
  # Clear error marker on success
  rm -f "$ERROR_MARKER" 2>/dev/null || true
  log_line INFO "PRE-FLIGHT OK: Tethering USB rilevato su Debian -> $detect_out"

  if [[ "$MODE" == "intranet" ]]; then
    out="$(ssh_debian "nohup setsid sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh activate $DURATION intranet >/dev/null 2>&1 &" 2>&1)"
  else
    # NOTA: niente "&" qui - "$(cmd &)" non stacca davvero il processo (la
    # subshell di command substitution termina comunque appena lanciato il
    # job, quindi non lo aspetta) e rende $? del tutto inaffidabile: rc
    # sarebbe sempre ~0 anche se ssh_debian fallisse, nascondendo gli errori.
    # usb_tether.sh in modalita' server ritorna comunque in fretta (il
    # watchdog lo stacca lui internamente), quindi va bene sincrono.
    out="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh activate $DURATION server" 2>&1)"
  fi
  rc=$?
  log_line INFO "EXEC Debian activate $MODE rc=$rc | $(printf '%s' "$out" | tail -c 500)"
  if (( rc != 0 )); then
    json_error "activate Debian fallito rc=$rc"
    return 0
  fi
  printf '{"state":"activating","mode":"%s","message":"Attivazione in corso..."}\n' "$MODE"
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
  # Qui non facciamo nulla - il restore Windows vero e proprio è in router_finish_restore_windows

  printf '{"state":"restoring","mode":"server","message":"Ripristino in corso..."}\n'
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
    still_active="$(ssh_router "iptables -t mangle -S TETHER_${ROUTER_MARK_LEAVE_ANCHOR} >/dev/null 2>&1 && echo 1 || echo 0" 2>/dev/null | tr -d '\r' | tail -1)"
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
  out="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh restore" 2>&1)"
  rc=$?
  log_line INFO "EXEC Debian restore rc=$rc | $(printf '%s' "$out" | tail -c 500)"
  if (( rc != 0 )); then
    json_error "restore Debian fallito rc=$rc"
    return 0
  fi
  printf '{"state":"restoring","mode":"server","message":"Ripristino in corso..."}\n'
}

case "$ACTION" in
  status)
    run_status
    ;;
  router_cutover_windows)
    router_cutover_windows
    ;;
  router_finish_restore_windows)
    router_finish_restore_windows
    ;;
  activate)
    if [[ "$HOST" == *"Windows"* ]]; then
      activate_windows
    else
      activate_debian
    fi
    ;;
  restore)
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
