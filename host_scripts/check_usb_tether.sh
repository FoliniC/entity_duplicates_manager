#!/bin/sh
LOG_DIR="/config/logs/usb_tether"
LOG_FILE="${LOG_DIR}/usb_tether_state.log"
STATE_FILE="${LOG_DIR}/.last_state"
mkdir -p "${LOG_DIR}"
check_tether_state() {
    if [ -e /sys/class/net/usb0/carrier ]; then
        carrier=$(cat /sys/class/net/usb0/carrier 2>/dev/null)
        if [ "${carrier}" = "1" ]; then
            echo "ON"
            return
        fi
    fi
    if ip link show usb0 2>/dev/null | grep -q "UP" && ip addr show usb0 2>/dev/null | grep -q "inet "; then
        echo "ON"
        return
    fi
    echo "OFF"
}
current_state=$(check_tether_state)
current_time=$(date '+%Y-%m-%d %H:%M:%S')
if [ ! -f "${STATE_FILE}" ]; then
    echo "${current_time} la connessione USB tethering è in stato ${current_state} fino alle ore ${current_time}" > "${LOG_FILE}"
    echo "${current_state}" > "${STATE_FILE}"
    exit 0
fi
last_state=$(cat "${STATE_FILE}")
if [ "${current_state}" != "${last_state}" ]; then
    echo "${current_time} la connessione USB tethering è in stato ${last_state} fino alle ore ${current_time}" >> "${LOG_FILE}"
    echo "${current_time} la connessione USB tethering è in stato ${current_state} fino alle ore ${current_time}" >> "${LOG_FILE}"
    echo "${current_state}" > "${STATE_FILE}"
else
    if [ -f "${LOG_FILE}" ] && [ -s "${LOG_FILE}" ]; then
        last_line=$(tail -n 1 "${LOG_FILE}")
        updated_line=$(echo "${last_line}" | sed "s/fino alle ore .*/fino alle ore ${current_time}/")
        head -n -1 "${LOG_FILE}" > "${LOG_FILE}.tmp" 2>/dev/null || true
        echo "${updated_line}" >> "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "${LOG_FILE}"
    fi
fi
