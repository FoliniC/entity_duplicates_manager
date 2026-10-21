#!/bin/sh
# Attiva il Tethering USB su Android via ADB (Redmi Note 11 Pro 5G, MIUI 13).
#
# LEZIONI 2026-10-21 (tutte verificate sul campo):
#  - le coordinate del toggle NON sono fisse (1546 -> 1523): le leggiamo dal
#    dump UI con uiautomator.
#  - "tr '>' '>\n'" NON funziona su busybox: usare sed 's/></>\n</g'.
#  - va fatta "force-stop" delle impostazioni prima di riaprire, altrimenti
#    l'intent viene consegnato all'istanza gia' aperta e lo schermo non
#    viene portato in primo piano (il dump restituisce il launcher).
#  - dopo "am start" la schermata puo' mettere qualche secondo a prendere
#    il focus: bisogna ASPETTARE che mCurrentFocus sia TetherSettings,
#    altrimenti il dump contiene la home e il parsing fallisce.
#  - lo schermo deve essere sveglio e senza keyguard, altrimenti il tap
#    non arriva.
#  - lo switch puo' risultare gia' "checked" mentre sys.usb.config non e'
#    rndis (stato desincronizzato): in quel caso va cyclato (off -> on).
#  - il router ha BUSYBOX awk: niente match() con array, uso index/substr/split.
export HOME=/root

ADB=/usr/bin/adb_router
SERIAL="69a47f6d3a61"
ACTIVITY=com.android.settings/.TetherSettings
UI=/data/local/tmp/tether_ui.xml

sh_() { $ADB -s $SERIAL shell "$1" 2>/dev/null | tr -d '\r'; }
cfg() { sh_ "getprop sys.usb.config"; }

dump_ui() {
    sh_ "uiautomator dump $UI" >/dev/null 2>&1
    sh_ "cat $UI" 2>/dev/null | sed 's/></>\n</g'
}

switch_pos() {
    dump_ui | awk '
      /text="Tethering USB"/ { f=1; next }
      f && /switch_widget/ {
        p = index($0, "bounds=")
        if (p > 0) {
          s = substr($0, p+8)
          gsub(/[^0-9]/, " ", s)
          split(s, b, " ")
          if (b[4] > 0) { printf "%d %d\n", (b[1]+b[3])/2, (b[2]+b[4])/2; exit }
        }
      }'
}

switch_checked() {
    dump_ui | awk '
      /text="Tethering USB"/ { f=1; next }
      f && /switch_widget/ {
        p = index($0, "checked=")
        if (p > 0) { s = substr($0, p+9, 5); gsub(/[^a-z]/, "", s); print s; exit }
      }'
}

# aspetta che TetherSettings abbia il focus, poi la legge
wait_settings() {
    i=0
    while [ $i -lt 15 ]; do
        FOCUS=$(sh_ "dumpsys window | grep mCurrentFocus")
        case "$FOCUS" in
            *TetherSettings*) return 0 ;;
        esac
        sleep 2
        i=$((i+1))
    done
    return 1
}

open_settings() {
    sh_ "am force-stop com.android.settings" >/dev/null 2>&1
    sleep 2
    sh_ "am start -n $ACTIVITY" >/dev/null 2>&1
    wait_settings
}

toggle() {
    POS=$(switch_pos)
    if [ -z "$POS" ]; then
        echo "WARN: switch Tethering USB non trovato nel dump UI"
        return 1
    fi
    X=$(echo "$POS" | cut -d' ' -f1)
    Y=$(echo "$POS" | cut -d' ' -f2)
    echo "Tap switch Tethering USB a ($X,$Y)"
    sh_ "input tap $X $Y" >/dev/null
    sleep 5
}

# --- stato attuale ---
USB_CFG=$(cfg)
if echo "$USB_CFG" | grep -q "rndis" && ip link show dev usb0 >/dev/null 2>&1; then
    echo "OK: USB tethering gia' attivo (config: $USB_CFG)"
    exit 0
fi

# --- preparazione schermo ---
sh_ "input keyevent KEYCODE_WAKEUP" >/dev/null
sleep 1
sh_ "wm dismiss-keyguard" >/dev/null
sleep 1

# --- apre le impostazioni di tethering ---
if ! open_settings; then
    echo "WARN: TetherSettings non ha preso il focus"
    exit 1
fi

# --- stato switch ---
CHECKED=$(switch_checked)
echo "Stato switch Tethering USB: ${CHECKED:-sconosciuto}"

if [ "$CHECKED" = "false" ]; then
    toggle
else
    echo "Switch ON ma RNDIS assente: ciclo off/on per forzare la riconfigurazione"
    toggle
    sleep 2
    open_settings
    toggle
fi

# --- verifica ---
USB_CFG=$(cfg)
if ! echo "$USB_CFG" | grep -q "rndis"; then
    sh_ "setprop sys.usb.config rndis,adb" >/dev/null 2>&1
    sleep 2
    USB_CFG=$(cfg)
fi

sh_ "input keyevent KEYCODE_BACK" >/dev/null

# --- aspetta usb0 ---
for i in $(seq 1 20); do
    if ip link show dev usb0 >/dev/null 2>&1; then
        ip link set usb0 up >/dev/null 2>&1
        echo "OK: USB Tethering attivo (config: $USB_CFG)"
        exit 0
    fi
    sleep 1
done

echo "WARN: Interface usb0 non trovata (config: $USB_CFG)."
exit 1
