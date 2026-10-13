#!/bin/bash
# USB Tethering State Monitor - runs on Debian host
# Uses ADB to check phone tethering state, writes to HA config directory
# Fallback: if ADB from Debian fails, try ADB from router via SSH

LOG_DIR="/home/carlo/docker/homeassistant/config/logs/usb_tether"
LOG_FILE="${LOG_DIR}/usb_tether_state.log"
STATE_FILE="${LOG_DIR}/.last_state"

mkdir -p "${LOG_DIR}"

# Check tethering state via ADB from Debian
check_tether_state_debian() {
    # Check if USB tethering setting is enabled
    usb_tethering=$(adb -s 127.0.0.1:5555 shell 'settings get global usb_tethering' 2>/dev/null | tr -d '\r')
    
    if [ "${usb_tethering}" != "1" ]; then
        echo "OFF"
        return 0
    fi
    
    # Check if rndis0 interface has an IP address (active connection)
    ip_addr=$(adb -s 127.0.0.1:5555 shell 'ip addr show rndis0 2>/dev/null | grep "inet "' 2>/dev/null | head -1)
    
    if [ -n "${ip_addr}" ]; then
        echo "ON"
        return 0
    fi
    
    echo "OFF"
    return 0
}

# Check tethering state via ADB from router (fallback)
check_tether_state_router() {
    # Check usb0 interface on router (carrier + IP)
    if ssh -o ConnectTimeout=5 -o BatchMode=yes root@192.168.0.11 "
        if [ -e /sys/class/net/usb0/carrier ]; then
            carrier=\$(cat /sys/class/net/usb0/carrier 2>/dev/null)
            if [ \"\${carrier}\" = \"1\" ]; then
                echo \"ON\"
                exit 0
            fi
        fi
        if ip link show usb0 2>/dev/null | grep -q \"UP\" && ip addr show usb0 2>/dev/null | grep -q \"inet \"; then
            echo \"ON\"
            exit 0
        fi
        echo \"OFF\"
    " 2>/dev/null; then
        return 0
    fi
    return 1
}

# Try Debian ADB first
current_state=$(check_tether_state_debian)
adb_exit_code=$?

# If Debian ADB failed (non-zero exit or empty result), try router fallback
if [ ${adb_exit_code} -ne 0 ] || [ -z "${current_state}" ]; then
    router_result=$(check_tether_state_router)
    if [ $? -eq 0 ] && [ -n "${router_result}" ]; then
        current_state="${router_result}"
    else
        # Both failed - keep last known state or default to OFF
        if [ -f "${STATE_FILE}" ]; then
            current_state=$(cat "${STATE_FILE}")
        else
            current_state="OFF"
        fi
    fi
fi

current_time=$(date '+%Y-%m-%d %H:%M:%S')

# If state file doesn't exist, this is first run - create initial log entry
if [ ! -f "${STATE_FILE}" ]; then
    echo "${current_time} la connessione USB tethering è in stato ${current_state} fino alle ore ${current_time}" > "${LOG_FILE}"
    echo "${current_state}" > "${STATE_FILE}"
    exit 0
fi

last_state=$(cat "${STATE_FILE}")

if [ "${current_state}" != "${last_state}" ]; then
    # State changed - log end of previous state and start of new state
    echo "${current_time} la connessione USB tethering è in stato ${last_state} fino alle ore ${current_time}" >> "${LOG_FILE}"
    echo "${current_time} la connessione USB tethering è in stato ${current_state} fino alle ore ${current_time}" >> "${LOG_FILE}"
    echo "${current_state}" > "${STATE_FILE}"
else
    # State unchanged - update the "fino alle ore" for current state
    if [ -f "${LOG_FILE}" ] && [ -s "${LOG_FILE}" ]; then
        last_line=$(tail -n 1 "${LOG_FILE}")
        updated_line=$(echo "${last_line}" | sed "s/fino alle ore .*/fino alle ore ${current_time}/")
        head -n -1 "${LOG_FILE}" > "${LOG_FILE}.tmp" 2>/dev/null || true
        echo "${updated_line}" >> "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "${LOG_FILE}"
    fi
fi
