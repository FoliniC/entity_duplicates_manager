#!/usr/bin/env bash
set -u

ACTION="${1:-status}"
MODE="${2:-server}"
HOST="${3:-Debian (192.168.0.3)}"
DURATION="${4:-60}"

LOG_FILE="/config/logs/usb_tether/usb_tether.log"
SSH_CM_DIR="/config/.ssh/cm"
WINDOWS_GW="192.168.0.8"
ROUTER_WAN_IF="usb0"
ROUTER_WAN_METRIC="10"
WINDOWS_ROUTE_METRIC="30"
ACTIVATE_GRACE_SECONDS="${USB_TETHER_ACTIVATE_GRACE_SECONDS:-120}"
RESTORE_GRACE_SECONDS="${USB_TETHER_RESTORE_GRACE_SECONDS:-180}"
RESTORE_SNAPSHOT_SECONDS="${USB_TETHER_RESTORE_SNAPSHOT_SECONDS:-5}"
RESTORE_MARK="0x88"
RESTORE_MARK_MASK="0xff"
RESTORE_TABLE="88"

mkdir -p "$SSH_CM_DIR" /config/logs/usb_tether

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
  nohup "$0" "$action" "$delay" "$HOST" "$DURATION" >/dev/null 2>&1 &
}

run_status() {
  local out rc line
  if [[ "$HOST" == *"Windows"* ]]; then
    out="$(ssh_windows "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action status" 2>&1)"
    rc=$?
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

activate_windows() {
  local out rc router_out router_rc
  out="$(ssh_windows "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action activate -MaxMinutes $DURATION -Mode $MODE" 2>&1)"
  rc=$?
  log_line INFO "EXEC Windows activate $MODE rc=$rc | $(printf '%s' "$out" | tail -c 500)"
  if (( rc != 0 )); then
    json_error "activate Windows fallito rc=$rc"
    return 0
  fi

  if [[ "$MODE" == "intranet" ]]; then
    router_out="$(ssh_router "ip route replace default via $WINDOWS_GW dev br-lan metric $WINDOWS_ROUTE_METRIC; ip route show default; true" 2>&1)"
    router_rc=$?
    log_line INFO "EXEC Router prepare Windows rc=$router_rc | $(printf '%s' "$router_out" | tail -c 500)"
    if (( router_rc != 0 )); then
      json_error "router via Windows fallito rc=$router_rc"
      return 0
    fi
    log_line INFO "TRANSIZIONE Windows intranet: WAN router $ROUTER_WAN_IF mantenuta per ${ACTIVATE_GRACE_SECONDS}s, poi cutover via $WINDOWS_GW"
    schedule_self router_cutover_windows "$ACTIVATE_GRACE_SECONDS"
  fi

  printf '{"state":"activating","mode":"%s","message":"Attivazione in corso..."}\n' "$MODE"
}

activate_debian() {
  local out rc
  if [[ "$MODE" == "intranet" ]]; then
    out="$(ssh_debian "nohup setsid sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh activate $DURATION intranet >/dev/null 2>&1 &" 2>&1)"
  else
    out="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh activate $DURATION server" 2>&1 &)"
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

  router_out="$(ssh_router "
    ip route replace default via $WINDOWS_GW dev br-lan table $RESTORE_TABLE;
    ip rule add fwmark $RESTORE_MARK lookup $RESTORE_TABLE pref $RESTORE_TABLE 2>/dev/null || true;
    iptables -t mangle -D PREROUTING -i br-lan -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-xmark $RESTORE_MARK/$RESTORE_MARK_MASK 2>/dev/null || true;
    iptables -t mangle -A PREROUTING -i br-lan -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-xmark $RESTORE_MARK/$RESTORE_MARK_MASK 2>/dev/null || true;
    sleep $RESTORE_SNAPSHOT_SECONDS;
    iptables -t mangle -D PREROUTING -i br-lan -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-xmark $RESTORE_MARK/$RESTORE_MARK_MASK 2>/dev/null || true;
    iptables -t mangle -D PREROUTING -i br-lan -j CONNMARK --restore-mark --nfmask $RESTORE_MARK_MASK --ctmask $RESTORE_MARK_MASK 2>/dev/null || true;
    iptables -t mangle -A PREROUTING -i br-lan -j CONNMARK --restore-mark --nfmask $RESTORE_MARK_MASK --ctmask $RESTORE_MARK_MASK;
    GW=\$(ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1);
    if [ -n \"\$GW\" ]; then
      ip route replace default via \"\$GW\" dev $ROUTER_WAN_IF metric $ROUTER_WAN_METRIC 2>/dev/null;
    else
      ifup wan >/dev/null 2>&1;
      sleep 2;
      GW=\$(ifstatus wan 2>/dev/null | jsonfilter -e '@.route[0].nexthop' 2>/dev/null | head -1);
      [ -n \"\$GW\" ] && ip route replace default via \"\$GW\" dev $ROUTER_WAN_IF metric $ROUTER_WAN_METRIC 2>/dev/null;
    fi;
    echo ROUTES;
    ip route show default;
    echo RULES;
    ip rule show | grep -E 'fwmark $RESTORE_MARK|lookup $RESTORE_TABLE' || true;
    true
  " 2>&1)"
  router_rc=$?
  log_line INFO "EXEC Router restore WAN with Windows flow preservation rc=$router_rc | $(printf '%s' "$router_out" | tail -c 700)"

  if (( router_rc != 0 )); then
    json_error "restore router WAN fallito rc=$router_rc"
    return 0
  fi
  log_line INFO "TRANSIZIONE restore Windows: connessioni esistenti marcate via $WINDOWS_GW per ${RESTORE_GRACE_SECONDS}s, nuove connessioni via $ROUTER_WAN_IF"
  schedule_self router_finish_restore_windows "$RESTORE_GRACE_SECONDS"
  printf '{"state":"restoring","mode":"server","message":"Ripristino in corso..."}\n'
}

router_cutover_windows() {
  local delay="${MODE:-$ACTIVATE_GRACE_SECONDS}" out rc
  case "$delay" in ''|*[!0-9]*) delay="$ACTIVATE_GRACE_SECONDS" ;; esac
  sleep "$delay"
  out="$(ssh_router "while ip route del default dev $ROUTER_WAN_IF metric $ROUTER_WAN_METRIC 2>/dev/null; do :; done; ip route show default; true" 2>&1)"
  rc=$?
  log_line INFO "EXEC Router delayed cutover Windows rc=$rc | $(printf '%s' "$out" | tail -c 500)"
}

router_finish_restore_windows() {
  local delay="${MODE:-$RESTORE_GRACE_SECONDS}" out rc router_out router_rc
  case "$delay" in ''|*[!0-9]*) delay="$RESTORE_GRACE_SECONDS" ;; esac
  sleep "$delay"
  out="$(ssh_windows "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Scripts/usb_tether.ps1 -Action restore" 2>&1)"
  rc=$?
  log_line INFO "EXEC Windows delayed restore rc=$rc | $(printf '%s' "$out" | tail -c 500)"
  router_out="$(ssh_router "
    iptables -t mangle -D PREROUTING -i br-lan -m conntrack --ctstate ESTABLISHED,RELATED -j CONNMARK --set-xmark $RESTORE_MARK/$RESTORE_MARK_MASK 2>/dev/null || true;
    iptables -t mangle -D PREROUTING -i br-lan -j CONNMARK --restore-mark --nfmask $RESTORE_MARK_MASK --ctmask $RESTORE_MARK_MASK 2>/dev/null || true;
    ip rule del fwmark $RESTORE_MARK lookup $RESTORE_TABLE pref $RESTORE_TABLE 2>/dev/null || true;
    ip route flush table $RESTORE_TABLE 2>/dev/null || true;
    ip route del default via $WINDOWS_GW dev br-lan metric $WINDOWS_ROUTE_METRIC 2>/dev/null;
    ip route show default;
    true
  " 2>&1)"
  router_rc=$?
  log_line INFO "EXEC Router delayed cleanup Windows route/marks rc=$router_rc | $(printf '%s' "$router_out" | tail -c 700)"
}

restore_debian() {
  local out rc
  out="$(ssh_debian "sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh restore" 2>&1 &)"
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
