#!/bin/sh
# USB Tethering State Monitor - runs on OpenWrt router
# Logs state changes to /config/logs/usb_tether/usb_tether.log

LOG_DIR="/config/logs/usb_tether"
LOG_FILE="${LOG_DIR}/usb_tether.log"
STATE_FILE="${LOG_DIR}/.last_state"

mkdir -p "${LOG_DIR}"

# Check usb0 interface state
check_tether_state() {
    # Check if usb0 exists and has carrier (connected)
    if [ -e /sys/class/net/usb0/carrier ]; then
        carrier=$(cat /sys/class/net/usb0/carrier 2>/dev/null)
        if [ "${carrier}" = "1" ]; then
            echo "ON"
            return
        fi
    fi
    # Also check if interface is up with IP
    if ip link show usb0 2>/dev/null | grep -q "UP" && ip addr show usb0 2>/dev/null | grep -q "inet "; then
        echo "ON"
        return
    fi
    echo "OFF"
}

current_state=$(check_tether_state)
current_time=$(date '+%Y-%m-%d %H:%M:%S')

# Read last state
last_state=""
if [ -f "${STATE_FILE}" ]; then
    last_state=$(cat "${STATE_FILE}")
fi

# If state changed, log the transition
if [ "${current_state}" != "${last_state}" ]; then
    if [ -n "${last_state}" ]; then
        # Log the end of previous state
        echo "${current_time} la connessione USB tethering è in stato ${last_state} fino alle ore ${current_time}" >> "${LOG_FILE}"
    fi
    # Update state file
    echo "${current_state}" > "${STATE_FILE}"
else:
    # State unchanged - update the "fino alle ore" for current state by rewriting last line
    if [ -f "${LOG_FILE}" ] && [ -s "${LOG_FILE}" ]; then
        # Get the last line and update its timestamp
        last_line=$(tail -n 1 "${LOG_FILE}")
        # Replace the timestamp at the end with current_time
        updated_line=$(echo "${last_line}" | sed "s/fino alle ore .*/fino alle ore ${current_time}/")
        # Replace last line in file
        head -n -1 "${LOG_FILE}" > "${LOG_FILE}.tmp" 2>/dev/null || true
        echo "${updated_line}" >> "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "${LOG_FILE}"
    fi
fi