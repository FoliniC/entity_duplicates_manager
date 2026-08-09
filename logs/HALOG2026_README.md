# HALog2026 — Unified Logging System

The **HALog2026** system robustly and centrally manages custom logs for Home Assistant, resolving boot validation issues through an event-based architecture.

## 📁 File Structure
- **Configuration**: `/config/logs/halog2026_config.json`
- **Core Library**: `/config/pyscript/lib/halog2026_lib.py`
- **Pyscript Service**: `/config/pyscript/halog2026_events_write.py`
- **Boot Manager**: `/config/automations/halog2026_boot_manager.yaml`

## 🛠️ How to Add a Log (YAML)
To log a message from an automation, do not call the service directly. Instead, send a subsystem-specific event:

```yaml
action:
  - event: fancoil_log_event  # Choose from: fancoil_log_event, scale_log_event, ev_log_event
    event_data:
      level: INFO
      message: "Your message here"
```

## ⚙️ Configuration (JSON)
You can modify the behavior of each log by editing `halog2026_config.json`:

| Parameter | Description |
|-----------|-------------|
| `archive` | `true` to enable automatic rotation |
| `rotation_type` | `size` (by dimension), `time` (by time), `both` (both) |
| `max_bytes` | Maximum size in bytes (e.g., 5242880 = 5MB) |
| `when` | Time interval: `midnight`, `Days`, `Hours`, `Weeks` |
| `interval` | The number of `when` units to wait before rotating (e.g., if `when` is `Days` and `interval` is 2, it rotates every 2 days) |
| `backup_count` | Number of historical files to keep (retention) |

## 🚀 Active Uses

### 1. Fancoil
- **Event**: `fancoil_log_event`
- **Destination**: `/config/logs/fancoil_events/fancoil_events.log`
- **Features**: Active archiving (5MB or midnight), keeps 10 files. Handles boot buffering.

### 2. Electric Vehicles (EV)
- **Event**: `ev_log_event`
- **Destination**: `/config/logs/EV/ev_events.log`
- **Features**: Archiving by size (2MB), keeps 5 files.

### 3. Scale
- **Event**: `scale_log_event`
- **Destination**: `/config/logs/scale/scale_events.log`
- **Features**: Weekly archiving (`when: Weeks`, `interval: 1`), keeps 4 files. Enriches logs with light status and power consumption.

### 4. System (Cron / Scripts)
- **Event**: `system_log_event`
- **Destination**: `/config/logs/system/system.log`
- **Source**: External shell scripts (e.g., `ha_update.sh`) or maintenance automations.
- **Features**: Daily rotation, keeps 100 files. Records container update outcomes and system tasks.
- **Updated**: 2026-06-03 - Added support for `ha_update.sh`.

### 5. Balcone (Light)
- **Event**: `balcone_log_event`
- **Destination**: `/config/logs/balcone/balcone_events.log`
- **Features**: Active archiving (2MB or midnight), keeps 100 files. Logs every state change of `switch.luce_balcone_switch_1` (`on` / `off` / `unavailable` / `unknown`), classifying the reason (physical/RF, web UI/app, automation, Wi-Fi/cloud dropout). Uses `WARNING` level for anomalous transitions (arrival from `unavailable` / `unknown`).
- **Updated**: 2026-06-23 - Fixed bug in the `variables` block (`context` is an object, accessed via attribute with `is defined` guard, not `.get()`).

### 6. Cucina (Lights)
- **Event**: `cucina_log_event`
- **Destination**: `/config/logs/cucina/cucina_events.log`
- **Features**: Active archiving (2MB or midnight), keeps 100 files. Logs every state change of `switch.luci_cucina_switch_1..4` (`on` / `off` / `unavailable` / `unknown`), classifying the reason (physical/RF, web UI/app, automation, Wi-Fi/cloud dropout). Uses `WARNING` level for anomalous transitions (arrival from `unavailable` / `unknown`).
- **Updated**: 2026-07-08 - Added to track unexplained switch-offs after Power-on behavior was set to "Last State".

### 7. USB Tether
- **Event**: `halog2026_write_event` with `subsystem: usb_tether` (fired from scripts and automations)
- **Destination**: `/config/logs/usb_tether/usb_tether.log`
- **Features**: Active archiving (1MB or midnight), keeps 30 files. Logs dashboard actions, guard blocks, state transitions, activation failures, and auto-restore events. The dashboard reads the latest lines through `sensor.usb_tether_log`, whose state stays short and whose attributes expose bounded log text. Like all other subsystems, USB tether scripts and automations fire the `halog2026_write_event` event instead of calling `pyscript.halog2026_write`, avoiding "service not found" validation errors at boot.
- **Updated**: 2026-08-08 - Scripts and automations now fire `halog2026_write_event` instead of calling the `pyscript.halog2026_write` service directly (fixes boot validation error).

---

# HALog2026 — Sistema di Logging Unificato

Il sistema **HALog2026** gestisce in modo robusto e centralizzato i log personalizzati per Home Assistant, risolvendo i problemi di validazione al boot tramite un'architettura basata su eventi.

## 📁 Struttura File
- **Configurazione**: `/config/logs/halog2026_config.json`
- **Libreria Core**: `/config/pyscript/lib/halog2026_lib.py`
- **Servizio Pyscript**: `/config/pyscript/halog2026_events_write.py`
- **Manager di Boot**: `/config/automations/halog2026_boot_manager.yaml`

## 🛠️ Come aggiungere un Log (YAML)
Per loggare un messaggio da un'automazione, non chiamare il servizio direttamente. Invia invece un evento specifico per il sottosistema:

```yaml
action:
  - event: fancoil_log_event  # Scegli tra: fancoil_log_event, scale_log_event, ev_log_event
    event_data:
      level: INFO
      message: "Il tuo messaggio qui"
```

## ⚙️ Configurazione (JSON)
Puoi modificare il comportamento di ogni log agendo su `halog2026_config.json`:

| Parametro | Descrizione |
|-----------|-------------|
| `archive` | `true` per abilitare la rotazione automatica |
| `rotation_type` | `size` (per dimensione), `time` (per tempo), `both` (entrambi) |
| `max_bytes` | Dimensione massima in bytes (es. 5242880 = 5MB) |
| `when` | Intervallo temporale: `midnight`, `Days` (giorni), `Hours` (ore), `Weeks` (settimane) |
| `interval` | Il numero di unità `when` da attendere prima della rotazione (es. se `when` è `Days` e `interval` è 2, ruota ogni 2 giorni) |
| `backup_count` | Numero di file storici da conservare (retention) |

## 🚀 Utilizzi Attivi

### 1. Fancoil
- **Evento**: `fancoil_log_event`
- **Destinazione**: `/config/logs/fancoil_events/fancoil_events.log`
- **Caratteristiche**: Archiviazione attiva (5MB o mezzanotte), tiene 10 file. Gestisce il buffering al boot.

### 2. Veicoli Elettrici (EV)
- **Evento**: `ev_log_event`
- **Destinazione**: `/config/logs/EV/ev_events.log`
- **Caratteristiche**: Archiviazione per dimensione (2MB), tiene 5 file.

### 3. Scale
- **Evento**: `scale_log_event`
- **Destinazione**: `/config/logs/scale/scale_events.log`
- **Caratteristiche**: Archiviazione settimanale (`when: Weeks`, `interval: 1`), tiene 4 file. Arricchisce il log con lo stato delle luci e la potenza assorbita.

### 4. Balcone (Luce)
- **Evento**: `balcone_log_event`
- **Destinazione**: `/config/logs/balcone/balcone_events.log`
- **Caratteristiche**: Archiviazione attiva (2MB o mezzanotte), tiene 100 file. Registra ogni cambio di stato di `switch.luce_balcone_switch_1` (`on` / `off` / `unavailable` / `unknown`), classificando il motivo (fisico/RF, interfaccia web/app, automazione, dropout Wi-Fi/cloud). Usa livello `WARNING` per le transizioni anomale (arrivo da `unavailable` / `unknown`).
- **Aggiornato**: 2026-06-23 - Corretto bug nel blocco `variables` (`context` è un oggetto, va acceso per attributo con guardia `is defined`, non con `.get()`).

### 5. Cucina (Luci)
- **Evento**: `cucina_log_event`
- **Destinazione**: `/config/logs/cucina/cucina_events.log`
- **Caratteristiche**: Archiviazione attiva (2MB o mezzanotte), tiene 100 file. Registra ogni cambio di stato di `switch.luci_cucina_switch_1..4` (`on` / `off` / `unavailable` / `unknown`), classificando il motivo (fisico/RF, interfaccia web/app, automazione, dropout Wi-Fi/cloud). Usa livello `WARNING` per le transizioni anomale (arrivo da `unavailable` / `unknown`).
- **Aggiornato**: 2026-07-08 - Aggiunto per tracciare spegnimenti non spiegati dopo aver impostato Power-on behavior su "Last State".

### 6. Sistema (Cron / Script)
- **Evento**: `system_log_event`
- **Destinazione**: `/config/logs/system/system.log`
- **Provenienza**: Script shell esterni (es: `ha_update.sh`) o automazioni di manutenzione.
- **Caratteristiche**: Rotazione quotidiana, tiene 100 file. Registra esiti aggiornamenti container e task di sistema.
- **Aggiornato**: 2026-06-03 - Aggiunto supporto per `ha_update.sh`.

### 7. USB Tether
- **Evento**: `halog2026_write_event` con `subsystem: usb_tether` (inviato da script e automazioni)
- **Destinazione**: `/config/logs/usb_tether/usb_tether.log`
- **Caratteristiche**: Archiviazione attiva (1MB o mezzanotte), tiene 30 file. Registra azioni dashboard, blocchi di guardia, transizioni di stato, fallimenti di attivazione e auto-restore. La dashboard legge le ultime righe tramite `sensor.usb_tether_log`, con stato corto e attributi limitati per il testo del log. Come tutti gli altri sottosistemi, gli script e le automazioni USB tether inviano l'evento `halog2026_write_event` invece di chiamare `pyscript.halog2026_write`, evitando errori di validazione "servizio non trovato" al boot.
- **Aggiornato**: 2026-08-08 - Script e automazioni ora inviano `halog2026_write_event` invece di chiamare direttamente il servizio `pyscript.halog2026_write` (corregge l'errore di validazione al boot).

---
**Note for maintenance / Nota per la manutenzione**: JSON changes are loaded automatically at the next rotation event or restart. Le modifiche al file JSON vengono caricate automaticamente al prossimo evento di rotazione o al riavvio.
