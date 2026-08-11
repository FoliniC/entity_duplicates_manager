# Configurazione Dashboard HA Clipboards
# Aggiungi questo alla tua configurazione Lovelace (UI o YAML)

# --- Opzione 1: Tramite UI (Consigliato) ---
# 1. Vai in Impostazioni > Dashboard > Risorse
# 2. Aggiungi risorsa: /local/ha_clipboards/ha-clipboards-card.js (tipo: JavaScript Module)
# 3. Crea una nuova vista o aggiungi a una esistente
# 4. Aggiungi scheda > Personalizzata: ha-clipboards-card
# 5. Configura: entity: sensor.ha_clipboards

# --- Opzione 2: YAML (configuration.yaml o lovelace.yaml) ---
# resources:
#   - url: /local/ha_clipboards/ha-clipboards-card.js
#     type: module
#
# views:
#   - title: Clipboards
#     icon: mdi:clipboard-text-multiple
#     cards:
#       - type: custom:ha-clipboards-card
#         entity: sensor.ha_clipboards

# --- Configurazione sensore (configuration.yaml) ---
# Dopo aver aggiunto il custom component, riavvia HA e aggiungi:
#
# sensor:
#   - platform: ha_clipboards

# --- Servizi disponibili ---
# ha_clipboards.create_attribute
#   name: "nome_attributo"
#
# ha_clipboards.set_active
#   name: "nome_attributo"
#
# ha_clipboards.save_text
#   text: "testo da salvare"
#
# ha_clipboards.delete_attribute
#   name: "nome_attributo"

# --- Esempio automazione per salvare da un input_text ---
# automation:
#   - alias: "Salva clipboard da input_text"
#     trigger:
#       - platform: state
#         entity_id: input_text.mio_testo
#     action:
#       - service: ha_clipboards.save_text
#         data_template:
#           text: "{{ states('input_text.mio_testo') }}"

# --- Esempio script per creare attributo da voce ---
# script:
#   crea_clipboard:
#     sequence:
#       - service: ha_clipboards.create_attribute
#         data:
#           name: "{{ nome_clipboard }}"