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

---
**Note for maintenance / Nota per la manutenzione**: JSON changes are loaded automatically at the next rotation event or restart. Le modifiche al file JSON vengono caricate automaticamente al prossimo evento di rotazione o al riavvio.
