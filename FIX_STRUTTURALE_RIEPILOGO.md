# Fix Strutturale Fancoil + Tuya - Riepilogo 2026-11-07

## Panoramica
Fix completato in due parti:
1. **Tuya LocalTuya entities unavailable** - Finestra camera grande (bf286f5f852a086ae6wltl) + sensori TH (th1a-th4d)
2. **Fancoil automations restructure** - Da mode:restart + wait_template perpetuo → trigger-based template sensors + automazioni mode:single

---

## PARTE 1: Fix Tuya LocalTuya Entities Unavailable

### Root Cause
LocalTuya tratta `device_sleep_time > 0` come **cloud-only device** (salta connessione locale, usa solo cloud polling).
- `cloud_polling_enabled: false` + `device_sleep_time: 60` = **nessuna fonte dati** → entities unavailable
- th1a aveva `device_sleep_time: null` → tentativi connessione locale falliti (Errno 113)

### Fix Applicati

#### finestra_camera_grande (bf286f5f852a086ae6wltl, IP 192.168.0.165)
1. Aggiunto IP/MAC a `tuya_selective_isolation.py` `is_battery_sensor` (detection contact/door/window/finestra/porta)
2. Eseguito `tuya_selective_isolation.py apply --strict-battery` → aggiunti 192.168.0.160 e 192.168.0.165 a nftables `battery_ips`
3. **Fix critico**: `core.config_entries` → `cloud_polling_enabled: true` (default) + `device_sleep_time: 60`
4. Clean entity registry (9 stale entities) + restart HA
5. **Risultato**: `binary_sensor.finestra_camera_grande_finestra_camera_grande` = "off" (available)

#### th1a (bfa9d781bf14faf268weol, IP 192.168.0.139)
- Allineato `device_sleep_time: 3600` (come th2b/th3c/th4d) → modalità cloud-only consistente
- Clean entity registry + restart HA
- **Risultato**: temperature 23.2°C, humidity 57%, battery 72% (tutti available)

#### th2b/th3c/th4d (IP 192.168.0.40/41/42)
- Già corretti: `device_sleep_time: 3600`, `cloud_polling_enabled: true` (default)
- Nessuna modifica necessaria

### Documentazione
- `TUYA_FINESTRA_CAMERA_GRANDE_FIX.md` - dettagli fix finestra_camera_grande
- `tuya_handshake.md` - credenziali/handshake (preservato)
- `tuya_selective_isolation.py` - script firewall selettivo (modificato)

---

## PARTE 2: Fix Strutturale Fancoil Automations

### Problema Originale
4 automazioni per zona (bagno, camera_grande, corridoio, cucina) con:
- `mode: restart`
- `wait_template` fino a 3 min
- `time_pattern` every 10 min
- **Risultato**: automation sempre "running" → warning "Stopping scripts running too long after shutdown"

### Soluzione: Trigger-Based Template Sensors (HA 2023.4+)

#### Architettura
```
┌─────────────────────────────────────────────────────────────┐
│  TEMPLATE SENSORS (computational logic)                     │
│  - sensor.fancoil_{zone}_fan_target                         │
│  - sensor.fancoil_{zone}_hvac_temp_mode                     │
│  - sensor.fancoil_{zone}_diff                               │
│  - sensor.fancoil_{zone}_stop_condition (binary)            │
│  - sensor.fancoil_{zone}_resume_allowed                     │
│  - sensor.fancoil_{zone}_main_available                     │
│  - sensor.fancoil_{zone}_fan_attuale_hw                     │
│  - sensor.fancoil_{zone}_temperature_difference             │
│  - sensor.fancoil_{zone}_hvac_mode_actual                   │
│  - sensor.fancoil_{zone}_init_done                          │
│  Triggers: state changes su input_select, input_number,     │
│  sensor, binary_sensor, switch entities                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  AUTOMATIONS (actuation only) - mode: single               │
│  Per zona: 4 automazioni v3                                 │
│  1. fanmode_dinamica_v3  - set fan_mode, init, stop, resume │
│  2. master_off_v3        - climate.turn_off su master OFF   │
│  3. entity_monitor_v3    - check availability, fire init    │
│  4. recovery_v3          - power cycle su anomaly detection │
└─────────────────────────────────────────────────────────────┘
```

#### File Creati/Modificati
| File | Descrizione |
|------|-------------|
| `yaml_generator/templates/fancoil_template_sensors.yaml` | 654 righe, trigger-based template sensors per 4 zone (combined trigger/sensor dict format per `!include`) |
| `yaml_generator/templates/fancoil_simplified_automations.yaml` | 1052 righe, template automazioni semplificate |
| `yaml_generator/fancoil_templates_master.yaml` | Patched: aggiunto `!include templates/fancoil_template_sensors.yaml` |
| `automations/bagno_automation.yaml` | Sostituito: 6 automazioni v3 (lista YAML diretta) |
| `automations/camera_grande_automation.yaml` | Sostituito: 4 automazioni v3 |
| `automations/corridoio_automation.yaml` | Sostituito: 4 automazioni v3 |
| `automations/cucina_automation.yaml` | Sostituito: 4 automazioni v3 |

#### Chiavi Tecniche
- **Template sensor format**: Combined trigger/sensor dict (NON lista di trigger blocks) per compatibilità `!include` in `template:`
- **Automation entity_id**: Derivato da `alias` → aggiunto "v3" per evitare collisioni con vecchie versioni
- **Mode**: Tutte `mode: single` (no restart, no parallel)
- **Trigger**: `state` (template sensors), `event` (initialization), `time_pattern` (recovery/monitor), `homeassistant.start`

#### Verifiche Post-Deploy
- ✅ 4 zone × fan_target sensors = "off" (base state)
- ✅ hvac_temp_mode = "heat", diff = 2.1°C, stop_condition = off
- ✅ 18 nuove automazioni v3 = state "on"
- ✅ Vecchie automazioni = state "unavailable" (sostituite)
- ✅ Tuya finestra_camera_grande = "off" (available)
- ✅ th1a = 21.0°C (available)
- ✅ Router nftables battery_ips = 7 IPs corretti

---

## Rollback Procedure

### Tuya Fix Rollback
```bash
# 1. Ripristina cloud_polling_enabled: false per finestra_camera_grande
#    Modifica core.config_entries per bf286f5f852a086ae6wltl
# 2. Rimuovi 192.168.0.160 e 192.168.0.165 da nftables battery_ips
ssh -i .ssh/router_key root@192.168.0.11 "nft delete element inet tuya_block battery_ips { 192.168.0.160, 192.168.0.165 }"
# 3. Ripristina device_sleep_time: null per th1a
# 4. Clean entity registry + restart HA
```

### Fancoil Automation Rollback
```bash
# 1. Ripristina vecchi file automation da backup (se disponibili)
# 2. Rimuovi !include templates/fancoil_template_sensors.yaml da fancoil_templates_master.yaml
# 3. Reload template sensors + restart HA
# 4. Le vecchie automazioni (se in entity registry) torneranno available
```

---

## Note Tecniche

### Template Sensor Include Format
HA richiede che i file inclusi via `template: !include` abbiano struttura **combined trigger/sensor dict**:
```yaml
trigger:
  - platform: state
    entity_id: ...
sensor:
  - name: ...
    ...
```
NON:
```yaml
template:
  - trigger: ...
    sensor: ...
```

### Automation Alias → Entity ID
HA genera `entity_id` da `alias` via slugify. Cambiare alias rompe reference in script/automazioni → usare suffisso "v3" per nuove versioni.

### LocalTuya Cloud-Only Behavior
| device_sleep_time | cloud_polling_enabled | Comportamento |
|-------------------|----------------------|---------------|
| > 0 (es. 60, 3600) | true (default) | Cloud polling ONLY, local skipped |
| > 0 | false | **NO DATA SOURCE** → unavailable |
| null/0 | true | Local connection attempted |
| null/0 | false | Local connection attempted |

Per dispositivi battery (contatti, sensori TH): **usare device_sleep_time > 0 + cloud_polling_enabled: true** + firewall selettivo per bloccare cloud outbound.

---

## Prossimi Passi (Opzionali)
1. Migrare automazioni Sala (attualmente vecchie) stessa architettura v3
2. Aggiungere test automatizzati per template sensors
3. Documentare fancoil_simplified_automations.yaml come reference per future zone