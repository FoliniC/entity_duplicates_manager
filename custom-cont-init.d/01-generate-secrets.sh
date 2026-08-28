#!/bin/bash
# Generate secrets.yaml and recorder.yaml from environment variables
# This runs at container startup before Home Assistant starts
# Reads secrets from /config/.env mounted from the host

set -e

CONFIG_DIR="/config"
ENV_FILE="/config/.env"

# Load environment from mounted .env file
if [ -f "$ENV_FILE" ]; then
    set -a
    . "$ENV_FILE"
    set +a
fi

# Default values if not in env
MYSQL_PASSWORD="${MYSQL_PASSWORD:-mariaDb}"
INFLUXDB_TOKEN="${INFLUXDB_TOKEN:-8evmkMtg_hEvAxcbZ8M8wHSlbDD0SqNkSSlCS6sT8jMxFm6QMqDyTDtwXmkEi6geo1N5nO7inT8a5_Iw7TrKjA==}"
INFLUXDB_BACKUP_TOKEN="${INFLUXDB_BACKUP_TOKEN:-poTKSA7Y5FRRgI4Bir-aS21FcdWq0N89WNlHwiIVl8m3DOUQkfsL7aF188ygKB7GRYwP5t0wLEoJnCbUAHXefA==}"
DUCKDNS_TOKEN="${DUCKDNS_TOKEN:-5ccf0276-b96f-44c8-a0f9-4a48784d8275}"
DUCKDNS_DOMAIN="${DUCKDNS_DOMAIN:-folini.duckdns.org}"
MQTT_USERNAME="${MQTT_USERNAME:-homeassistant}"
MQTT_PASSWORD="${MQTT_PASSWORD:-jo1ahleiP1Voh2Gie5aeP5oub4aeko8Kaeka1hudeigohbahshoo0aepoot9pif5}"
WIFI_SSID="${WIFI_SSID:-CPE_2.4G_112E90}"
WIFI_PASSWORD="${WIFI_PASSWORD:-Qv&#$SG8MGb1i}"
GENAI_GROUNDED_TOKEN="${GENAI_GROUNDED_TOKEN:-jKL0i57w9EdfAJmgYkJjjjDDBoHdHU-v_3i2tcDK434}"
GENAI_GROUNDED_URL="${GENAI_GROUNDED_URL:-http://127.0.0.1:8010/ask}"

# Generate secrets.yaml
cat > "$CONFIG_DIR/secrets.yaml" <<SECUREOF
# AUTO-GENERATED FROM .env - DO NOT EDIT DIRECTLY
# Edit /home/carlo/docker/.env on the host instead
# This file is already excluded from git via .gitignore

some_password: welcome
duckdns_domain: "$DUCKDNS_DOMAIN"
duckdns_token: "$DUCKDNS_TOKEN"
influxdb_token: "$INFLUXDB_TOKEN"
influxdb_backup_token: "$INFLUXDB_BACKUP_TOKEN"
mariadb_password: "$MYSQL_PASSWORD"
mqtt_username: "$MQTT_USERNAME"
mqtt_password: "$MQTT_PASSWORD"
wifi_ssid: "$WIFI_SSID"
wifi_password: "$WIFI_PASSWORD"
genai_grounded_url: "$GENAI_GROUNDED_URL"
genai_grounded_token: "$GENAI_GROUNDED_TOKEN"
SECUREOF

echo "Generated $CONFIG_DIR/secrets.yaml"

# Generate recorder.yaml
# Note: Home Assistant does NOT support !secret inside db_url connection strings in HA recorder config,
# so we use the actual password value directly
cat > "$CONFIG_DIR/recorder.yaml" <<RECEOF
# AUTO-GENERATED FROM .env - DO NOT EDIT DIRECTLY
# Edit /home/carlo/docker/.env on the host instead
# Note: !secret is not supported inside db_url connection strings in HA recorder config

db_url: mysql://homeassistant:${MYSQL_PASSWORD}@192.168.0.3:3306/homeassistant
auto_purge: true
purge_keep_days: 10
commit_interval: 1
exclude:
  entity_globs:
    - sensor.*_diagnostic_*
    - sensor.*_last_reset
    - sensor.*_update_category
    - sensor.*_update_version
RECEOF

echo "Generated $CONFIG_DIR/recorder.yaml"