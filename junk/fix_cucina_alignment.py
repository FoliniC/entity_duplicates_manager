
# Script di correzione e allineamento Cucina

# 1. Pulizia Offset (rimuove il float infinitesimale)
hass.states.set("input_number.fancoil_cucina_sp_offset", "0.0")

# 2. Trigger Automazione di Allineamento
# Questo forza la rilettura delle condizioni e applica il setpoint corretto
hass.services.call("automation", "trigger", {"entity_id": "automation.fancoil_cucina_allinea_master"}, False)

# 3. Log dell'azione
logger.info("Eseguita correzione offset e allineamento forzato per Cucina")
