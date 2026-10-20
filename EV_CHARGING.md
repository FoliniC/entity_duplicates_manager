# EV Charging System - Documentazione

## Panoramica
Sistema di ricarica VE per auto elettrica via Wallbox Prism, gestito da Home Assistant con automazioni dedicate.

---

## File Principali

### Configurazione Entità (`yaml_generator/`)
| File | Entità | Descrizione |
|------|--------|-------------|
| `input_select/ev_charge_2025.yaml` | `input_select.ev_charge_2025_mode` | Modalità: **Manuale** / **Automatico** (senza `initial` → usa RestoreEntity nativo) |
| `input_boolean/ev_charge_2025.yaml` | `ev_charge_2025_charging_active` | Avvia/ferma ricarica |
| | `ev_charge_2025_no_grid` | Escludi rete (solo solare/batteria) |
| | `ev_charge_2025_no_grid_2025` | **Bypass protezione BYD** (forza ricarica anche se SOC ≤ soglia) |
| `input_number/ev_charge_2025.yaml` | `ev_charge_2025_byd_protection_soc` | Soglia protezione BYD (default 10%) |
| | `ev_charge_2025_manual_power_kw` | Potenza fissa in modalità Manuale (kW) |
| | `ev_charge_2025_target_soc` | SOC target veicolo |
| | `ev_charge_2025_grid_max_power` | Max potenza da rete (kW) |
| | `ev_charge_2025_byd_max_discharge_power` | Max scarica BYD (W) |

### Automazioni (`automations/`)
| File | ID | Funzione |
|------|-----|----------|
| `ev_charge_2025_force_save_state.yaml` | `ev_charge_2025_force_save_state` | **Persistenza immediata** - chiama `homeassistant.save_persistent_states` su ogni cambio entità principali |
| `generated_automations/ev_charge_2025_automation.yaml` | `ev_charge_2025_control` | Logica principale: calcolo `w_disponibile`, START/STOP, protezione BYD, boot sync |
| `ev_charge_2025_send_current.yaml` | `ev_charge_2025_send_current` | Pubblica corrente (A) su MQTT `prism/set_current` ogni 10s |
| `ev_charge_2025_persistence.yaml` | `ev_charge_2025_save_state` | Backup storico su file (halog) |

### Dashboard (`ui/`)
| File | Descrizione |
|------|-------------|
| `ev_charge_control_2025.yaml` | Dashboard Lovelace con toggle Manuale/Automatico, slider, diagnostica BYD, flag bypass |

---

## Logica di Ricarica

### Modalità Automatico
- `w_disponibile = solare + batteria (se SOC > soglia) - carichi_casa`
- Se `w_disponibile ≥ 6A` → avvia ricarica
- Adatta corrente ogni 10s
- **Protezione BYD**: se `byd_soc ≤ byd_protection_soc` → STOP (salvo `no_grid_2025=ON`)

### Modalità Manuale
- Usa `manual_power_kw` fissa (convertita in A)
- Ignora produzione/consumi
- **Protezione BYD**:
  - `Escludi Rete=ON` → protezione ATTIVA
  - `Escludi Rete=OFF` (usa rete) → protezione **DISATTIVATA**
  - `Forza Ricarica BYD=ON` → bypass totale

### Flag Bypass
| Flag | Effetto |
|------|---------|
| `no_grid` | Solo solare/batteria, protezione BYD attiva |
| `no_grid_2025` | Ignora soglia BYD, ricarica sempre |

---

## Persistenza Stato (Fix 2026-10-19)

### Problema
Al riavvio HA, `input_select.ev_charge_2025_mode` tornava su "Automatico" anche se impostato su "Manuale".

### Causa
- `initial: "Automatico"` nel file YAML sovrascriveva lo stato ripristinato
- `core.restore_state` salvato solo periodicamente (~30s) o allo spegnimento pulito

### Soluzione (2 parti)

#### 1. Rimosso `initial` da `yaml_generator/input_select/ev_charge_2025.yaml`
```yaml
ev_charge_2025_mode:
  name: "Modalità Ricarica"
  options:
    - "Manuale"
    - "Automatico"
  icon: mdi:ev-station
  # initial: "Automatico"  ← RIMOSSO
```
Senza `initial`, HA usa **RestoreEntity** nativo → legge da `core.restore_state`.

#### 2. Automation persistenza immediata (`ev_charge_2025_force_save_state.yaml`)
```yaml
trigger:
  - platform: state
    entity_id:
      - input_select.ev_charge_2025_mode
      - input_boolean.ev_charge_2025_charging_active
      - input_boolean.ev_charge_2025_no_grid
      - input_boolean.ev_charge_2025_no_grid_2025
      - input_number.ev_charge_2025_manual_power_kw
      # ... tutti gli slider
action:
  - service: homeassistant.save_persistent_states
```
Forza scrittura **immediata** su disco ad ogni cambio.

### Risultato
- Cambio "Automatico" → "Manuale" in dashboard
- Automation trigger → `save_persistent_states` → scrive su `.storage/core.restore_state`
- Riavvio immediato → ripristina "Manuale" ✓

---

## Avvio/Ripristino (Boot)

1. Event `homeassistant.start` → trigger automation principale
2. Delay 10s (attesa sensori MQTT/Prism)
3. `force_current_sync` con `is_boot=true`:
   - Legge stati da `core.restore_state` (già ripristinati)
   - Pubblica modalità + corrente su MQTT
   - Ricarica riparte **senza interruzione** con parametri precedenti

---

## Reboot Corretto
Per garantire persistenza:
- **HA UI** → Developer Tools → YAML → **Restart** (spegnimento pulito, salva stato)
- **`docker stop homeassistant`** (con `stop_grace_period: 60s` in docker-compose)
- **NON** `docker restart` (timeout 10s → SIGKILL prima del salvataggio)

---

## Entità MQTT
- `prism/set_current` → Comando corrente (A) per Wallbox
- `prism/status` → Stato Wallbox (corrente, potenza, energia)
- Sensori solari/batteria/carichi → Input per calcolo `w_disponibile`

---

## Note Tecniche
- **Protezione BYD soglia**: `input_number.ev_charge_2025_byd_protection_soc` (default 10%)
- **Corrente minima avvio**: 6A (~1.4kW)
- **Aggiornamento corrente**: Ogni 10s via `ev_charge_2025_send_current`
- **Diagnostica dashboard**: Mostra "Batteria BYD sotto soglia" solo se protezione attiva