#!/bin/bash

# ==============================================================================
# SCRIPT DI AGGIORNAMENTO AUTOMATICO HOME ASSISTANT
# ==============================================================================
# Eseguito ogni 5 del mese alle 03:00 tramite cron
# ==============================================================================

# CONFIGURAZIONE
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
DOCKER_DIR="/home/carlo/docker"
HA_URL="http://localhost:8123"
# TOKEN PRESERVATO
HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZDQ0ZGFmMDk1MDk0ZmI3OGU5YmFiNDFlNTA1YTE4OCIsImlhdCI6MTc4MDY2MTc4MiwiZXhwIjoyMDk2MDIxNzgyfQ.FNSWdfYbUxxX7h0CZpfSCZ9GGos5NYJoN4t7H3P_Bt0"

cd "$DOCKER_DIR" || exit 1

# Funzione per loggare su HALog2026
send_log() {
    local level=$1
    local msg=$2
    echo "[LOG $level] $msg"
    curl -s -X POST \
      -H "Authorization: Bearer $HA_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"event_type\": \"system_log_event\", \"level\": \"$level\", \"message\": \"[ha_update.sh] $msg\"}" \
      "$HA_URL/api/events/system_log_event" > /dev/null
}

# 0. Log iniziale
send_log "INFO" "Avvio verifica aggiornamento Home Assistant..."

# 1. Recupera ID immagine attuale del container e versione
CURRENT_IMAGE_ID=$(docker inspect homeassistant --format='{{.Image}}' 2>/dev/null)
echo "Recupero versione attuale..."
OLD_VERSION=$(docker exec homeassistant python3 -c 'from homeassistant.const import __version__; print(__version__)' 2>/dev/null)
if [ -z "$OLD_VERSION" ]; then
    OLD_VERSION="Sconosciuta"
fi

echo "Versione attuale: $OLD_VERSION (Image ID: ${CURRENT_IMAGE_ID:0:12})"

# 2. Pull dell'immagine 'stable'
echo "Controllo nuove immagini (docker compose pull)..."
docker compose pull homeassistant > /dev/null 2>&1

# 3. Recupera ID della nuova immagine scaricata
LATEST_IMAGE_ID=$(docker inspect ghcr.io/home-assistant/home-assistant:stable --format='{{.Id}}' 2>/dev/null)

# 4. Confronto ID per decidere se aggiornare
if [ "$CURRENT_IMAGE_ID" == "$LATEST_IMAGE_ID" ]; then
    echo "Il sistema è già aggiornato (Image ID identico)."
    send_log "INFO" "Home Assistant è già aggiornato alla versione $OLD_VERSION."
    exit 0
fi

# 5. Effettua l'aggiornamento (Restart con nuova immagine)
echo "Nuova immagine rilevata (${LATEST_IMAGE_ID:0:12}). Aggiornamento in corso..."
UP_OUTPUT=$(docker compose up -d homeassistant 2>&1)

if [ $? -eq 0 ]; then
    echo "Aggiornamento completato. Attendo avvio (30s) per verifica versione..."
    sleep 30
    NEW_VERSION=$(docker exec homeassistant python3 -c 'from homeassistant.const import __version__; print(__version__)' 2>/dev/null)
    MSG="✅ Home Assistant aggiornato con successo! Da $OLD_VERSION a $NEW_VERSION"
    TITLE="Aggiornamento Sistema"
    LEVEL="INFO"
else
    MSG="❌ Errore durante l'aggiornamento: $(echo "$UP_OUTPUT" | tail -n 1)"
    TITLE="ERRORE Aggiornamento"
    LEVEL="ERROR"
fi

# 6. Notifica e Log finale
curl -s -X POST \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"$TITLE\", \"message\": \"$MSG\", \"notification_id\": \"ha_update_check\"}" \
  "$HA_URL/api/services/persistent_notification/create" > /dev/null

send_log "$LEVEL" "$MSG"
echo "$MSG"
