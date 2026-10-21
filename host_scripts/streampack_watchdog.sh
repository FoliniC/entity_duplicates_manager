#!/bin/sh
# StreamPack watchdog: mantiene vivo lo stream.
#
# 1) Se il tethering USB e' caduto (sys.usb.config senza "rndis"), lo ripristina
#    chiamando enable_usb_tether.sh: senza RNDIS l'app non puo' pubblicare.
# 2) Se l'app non e' in esecuzione, la rilancia IN FOREGROUND.
#
# PERCHE' IL FLAG -f 0x10000000 (FLAG_ACTIVITY_NEW_TASK):
# l'avvio con "am start -n ..." normale mette l'app in BACKGROUND, e Android
# (MIUI) rifiuta l'apertura della camera in background:
#   "REJECT device 0 client ... cannot open camera \"0\" from background"
# Inoltre il vendor camera (CamX) chiude il client e il processo riceve
# SIGKILL (ApplicationExitInfo: reason=2 SIGNALED, status=9).
# Con FLAG_ACTIVITY_NEW_TASK l'Activity resta in foreground, la camera si
# apre e lo streaming regge.
#
# Non tocca la rete del telefono a mano: ripristina solo il tethering che
# il telefono stesso ha disattivato, e riavvia l'app.
ADB=/usr/bin/adb_router
SERIAL=69a47f6d3a61
PKG=io.github.thibaultbee.streampack.app
LOG=/tmp/streampack_watchdog.log

log() { echo "[$(date "+%Y-%m-%d %H:%M:%S")] $*" >> "$LOG"; }

if ! $ADB devices 2>/dev/null | grep -q "^${SERIAL}[[:space:]].*device$"; then
  exit 0
fi

# --- 1. tethering USB ---
USB_CFG=$($ADB -s $SERIAL shell "getprop sys.usb.config" 2>/dev/null | tr -d '\r')
if ! echo "$USB_CFG" | grep -q "rndis"; then
  log "Tethering USB non attivo (config: $USB_CFG): ripristino"
  /usr/bin/enable_usb_tether.sh >/dev/null 2>&1
  sleep 5
  USB_CFG=$($ADB -s $SERIAL shell "getprop sys.usb.config" 2>/dev/null | tr -d '\r')
  if echo "$USB_CFG" | grep -q "rndis"; then
    log "Tethering USB ripristinato (config: $USB_CFG)"
  else
    log "ERRORE: ripristino tethering fallito (config: $USB_CFG)"
    exit 1
  fi
fi

# --- 2. app ---
PID=$($ADB -s $SERIAL shell "pidof $PKG" 2>/dev/null | tr -d '\r')
if [ -n "$PID" ]; then
  exit 0
fi

log "StreamPack non in esecuzione: riavvio in foreground"
$ADB -s $SERIAL shell "am start -n $PKG/.MainActivity -f 0x10000000" >/dev/null 2>&1
sleep 4
NEWPID=$($ADB -s $SERIAL shell "pidof $PKG" 2>/dev/null | tr -d '\r')
if [ -n "$NEWPID" ]; then
  log "StreamPack riavviato (foreground), PID=$NEWPID"
else
  log "ERRORE: riavvio fallito"
fi
