#!/bin/bash
# Generate recorder configuration from environment variables
# This runs at container startup before Home Assistant starts

set -e

RECORDER_FILE="/config/recorder.yaml"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-mariaDb}"

# Write file directly with proper substitution
cat > "$RECORDER_FILE" <<EOF
# AUTO-GENERATED FROM ENVIRONMENT VARIABLES - DO NOT EDIT DIRECTLY
# Edit .env in the docker-compose directory instead

recorder:
  db_url: mysql://homeassistant:${MYSQL_PASSWORD}@192.168.0.3/homeassistant
  exclude:
    entities:
      - automation.fancoil_bagno_fanmode_dinamica
      - automation.fancoil_camera_grande_fanmode_dinamica
      - automation.fancoil_cucina_fanmode_dinamica_2
      - automation.fancoil_corridoio_fanmode_dinamica
      - automation.fancoil_sala_fanmode_dinamica
      - automation.fancoil_camera_fanmode_dinamica
      - sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_voltaggio
      - sensor.energia_inviata_rete_giornaliera_alfa
      - sensor.energia_inviata_rete_mensile_alfa
      - sensor.energia_inviata_rete_annuale_alfa
      - sensor.energia_prelevata_rete_giornaliera_alfa
      - sensor.energia_prelevata_rete_mensile_alfa
      - sensor.energia_prelevata_rete_annuale_alfa
      - sensor.produzione_solare_giornaliera_alfa
      - sensor.produzione_solare_mensile_alfa
      - sensor.produzione_solare_annuale_alfa
    entity_globs:
      - automation.fancoil_*sincronizza_switch_principale
      - sensor.watchman_*
      - sensor.statistics_*variance
      - sensor.*_voltaggio
      - sensor.*_voltage
  purge_keep_days: 30
  commit_interval: 30
EOF

echo "Generated $RECORDER_FILE from environment variables"