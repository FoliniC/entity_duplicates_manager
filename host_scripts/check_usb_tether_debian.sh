#!/bin/bash
# USB Tethering State Monitor - runs on Debian host
# Uses ADB to check phone tethering state, writes to HA config directory
# Fallback: if ADB from Debian fails, try ADB from router via SSH
# Debounce: requires 2 consecutive checks with same result before logging state change
# HA readiness: skip check if Home Assistant is starting up

LOG_DIR="/home/carlo/docker/homeassistant/config/logs/usb_tether"
LOG_FILE="${LOG_DIR}/usb_tether_state.log"
STATE_FILE="${LOG_DIR}/.last_state"
DEBOUNCE_FILE="${LOG_DIR}/.debounce_state"
DEBOUNCE_COUNT_FILE="${LOG_DIR}/.debounce_count"

mkdir -p "${LOG_DIR}"

# Check if Home Assistant is fully ready (not starting up)
check_ha_ready() {
    # Quick check: HA API responds (not connection refused/timeout)
    # 401 = unauthorized but API is up; 000/timeout = starting or down
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 http://192.168.0.3:8123/api/ 2>/dev/null)
    if [ "${http_code}" = "000" ] || [ -z "${http_code}" ]; then
        return 1  # HA not ready
    fi
    return 0  # HA ready
}

# Skip if HA is starting up
if ! check_ha_ready; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Home Assistant not ready, skipping tether check" >> "${LOG_DIR}/monitor.log"
    exit 0
fi

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
    # State appears changed - apply debounce
    debounce_state=""
    debounce_count=0
    
    if [ -f "${DEBOUNCE_FILE}" ]; then
        debounce_state=$(cat "${DEBOUNCE_FILE}")
    fi
    if [ -f "${DEBOUNCE_COUNT_FILE}" ]; then
        debounce_count=$(cat "${DEBOUNCE_COUNT_FILE}")
    fi
    
    if [ "${debounce_state}" = "${current_state}" ]; then
        debounce_count=$((debounce_count + 1))
    else
        debounce_state="${current_state}"
        debounce_count=1
    fi
    
    echo "${debounce_state}" > "${DEBOUNCE_FILE}"
    echo "${debounce_count}" > "${DEBOUNCE_COUNT_FILE}"
    
    # Require 2 consecutive checks with same new state
    if [ ${debounce_count} -ge 2 ]; then
        # Confirmed state change - log ONLY the new state
        echo "${current_time} la connessione USB tethering è in stato ${current_state} fino alle ore ${current_time}" >> "${LOG_FILE}"
        echo "${current_state}" > "${STATE_FILE}"
        # Clear debounce
        rm -f "${DEBOUNCE_FILE}" "${DEBOUNCE_COUNT_FILE}"
    fi
    # If debounce not met yet, don't update log, don't update state file
else
    # State unchanged - clear any pending debounce and update "fino alle ore"
    rm -f "${DEBOUNCE_FILE}" "${DEBOUNCE_COUNT_FILE}"
    
    if [ -f "${LOG_FILE}" ] && [ -s "${LOG_FILE}" ]; then
        last_line=$(tail -n 1 "${LOG_FILE}")
        updated_line=$(echo "${last_line}" | sed "s/fino alle ore .*/fino alle ore ${current_time}/")
        head -n -1 "${LOG_FILE}" > "${LOG_FILE}.tmp" 2>/dev/null || true
        echo "${updated_line}" >> "${LOG_FILE}.tmp"
        mv "${LOG_FILE}.tmp" "${LOG_FILE}"
    fi
fi
