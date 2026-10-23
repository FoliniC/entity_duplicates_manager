# Sistema climatizzazione fancoil

Questo documento descrive la logica generata da `yaml_generator/generate_fancoil_climates.py` per il sistema di climatizzazione a fancoil.

## Sorgenti e file generati

La configurazione delle stanze parte da `yaml_generator/fancoil_vars.yaml`.

I template principali sono:

- `yaml_generator/templates/fancoil_automation.j2`: automazioni stanza, calcolo velocita, guardie globali, recovery.
- `yaml_generator/templates/fancoil_climate.j2`: climate template per ogni stanza.
- `yaml_generator/templates/fancoil_sensors.j2`: sensori di supporto per temperatura, delta e modalita.
- `yaml_generator/templates/fancoil_binary_sensors.j2`: sensori binari di stop e stato.
- `yaml_generator/templates/fancoil_master_input_booleans.j2`: helper booleani master.
- `yaml_generator/templates/fancoil_room_input_*`: helper per stanza.

I file operativi generati sono in:

- `automations/fancoil_generated_automations/*_automation.yaml`
- `yaml_generator/generated_climates/`
- `yaml_generator/managed_sensors/`
- `yaml_generator/managed_binary_sensors/`
- `yaml_generator/input_boolean/`, `input_number/`, `input_select/`, `input_datetime/`, `input_text/`

Le modifiche manuali alla logica stanza vanno fatte nel template `.j2`, poi si rigenerano i file. Modificare solo i file generati espone al rischio di perdere le correzioni alla generazione successiva.

## Entita globali

Le entita globali principali sono:

- `switch.attiva_fancoil`: consenso generale ai fancoil.
- `switch.attiva_pdc`: consenso PDC.
- `switch.attiva_pompa_circolazione`: consenso pompa circolazione.
- `input_select.fancoil_system_hvac_mode`: modalita master del sistema (`heat`, `cool`, `dry`, `off`).
- `input_boolean.fancoil_deumidificazione`: abilita il comportamento di deumidificazione.
- `binary_sensor.pdc_acqua_calda`: blocco/limitazione quando l'acqua PDC e calda.
- `binary_sensor.fancoil_circuit_temp_invalid`: stato temperatura circuito non valida.

## Rilevamento automatico finestra cucina

La cucina utilizza un sensore di contatto automatico `binary_sensor.contact_sensor_doorcontact_state` per rilevare lo stato della finestra, eliminando la necessità dell'`input_boolean.finestra_cucina_aperta` manuale.

Il sensore comunica di sua iniziativa solo quando la porta della finestra viene aperta o chiusa. In condizioni normali il sensore risulta non accessibile (unavailable).

Quando `window_contact_sensor` è definito per una stanza in `fancoil_vars.yaml`:

- non viene creato l'`input_boolean.finestra_<stanza>_aperta`;
- tutte le automazioni e i sensori usano il `binary_sensor` di contatto come sorgente dello stato finestra;
- il dashboard mostra lo stato del sensore di contatto direttamente.

## `system_enabled`

`system_enabled` e una variabile interna alle automazioni stanza, non una entity Home Assistant.

Vale `true` solo quando tutte queste condizioni sono vere:

```jinja
is_state('switch.attiva_fancoil', 'on')
and is_state('switch.attiva_pdc', 'on')
and is_state('switch.attiva_pompa_circolazione', 'on')
```

Quando `system_enabled=false`:

- il target ventola stanza diventa `off`;
- le automazioni spengono i quattro rele a valle (`switch_1..4`);
- il `fan_mode` del climate stanza viene portato a `off`;
- init e resume delle velocita vengono fermati;
- lo Stox principale resta alimentato, per mantenere disponibili temperatura e umidita.

## Stox e rele stanza

Ogni stanza ha uno switch principale:

```text
switch.stox_fancoil_<stanza>_switch
```

Questo alimenta il device con i quattro rele e deve restare acceso in condizioni normali, anche quando `system_enabled=false`, per continuare a leggere temperatura e umidita.

I quattro rele stanza sono:

```text
switch.fancoil_<stanza>_switch_1
switch.fancoil_<stanza>_switch_2
switch.fancoil_<stanza>_switch_3
switch.fancoil_<stanza>_switch_4
```

La mappa hardware delle velocita e:

```text
[0,0,0,0] = off
[0,0,0,1] = idle
[1,0,0,1] = low
[0,1,0,1] = medium
[0,0,1,1] = high
altro     = unknown
```

Quando il sistema globale e disabilitato, tutti i quattro rele devono essere `off`. Lo Stox principale invece non viene spento dalla guardia globale.

## Calcolo del target ventola

Il target stanza viene calcolato da:

- modalita stanza (`sensor.fancoil_<stanza>_hvac_temp_mode`);
- differenza temperatura/setpoint (`sensor.fancoil_<stanza>_temperature_difference`);
- soglie `input_number.fan_distance_*`;
- stop condition;
- deumidificazione;
- stato acqua calda PDC;
- `system_enabled`.

La prima guardia e `system_enabled`: se e falso, il target e `off` indipendentemente dal delta temperatura.

## Inizializzazione e reload

Le automazioni stanza reagiscono a:

- cambi di sensori stanza;
- cambi di `switch.attiva_fancoil`, `switch.attiva_pdc`, `switch.attiva_pompa_circolazione`;
- evento `automation_reloaded`;
- evento `fancoil_start_initialization`;
- trigger periodico da 10 minuti.

Al reload o al riavvio, se il sistema globale non e abilitato, la guardia globale spegne i rele a valle e ferma l'automazione prima di init/resume.

## Recovery e power cycle Stox

La recovery `Ripristino anomalie (Temp/Speed)` puo spegnere e riaccendere lo Stox per 10 secondi.

Questo comportamento e intenzionale: serve a recuperare casi in cui il device con i rele non risponde correttamente. La recovery non deve essere bloccata da `system_enabled=false`.

I casi gestiti sono:

- `temp_stuck`: temperatura ferma mentre la stanza dovrebbe lavorare e la velocita hardware e `low`, `medium` o `high`;
- `speed_mismatch`: target diverso dallo stato hardware per un tempo prolungato;
- `global_disabled_hw_stuck`: sistema globale disabilitato ma rele hardware ancora diversi da `off`.

Nel caso `global_disabled_hw_stuck`, la recovery puo comunque ciclare lo Stox per sbloccare il device, anche se normalmente lo Stox deve restare acceso.

## Logging

Gli eventi fancoil sono scritti tramite evento `fancoil_log_event`, gestito dal sistema HALog2026 documentato in `logs/HALOG2026_README.md`.

Il log operativo principale e:

```text
logs/fancoil_events/fancoil_events.log
```

I messaggi rilevanti per questa logica includono:

- `State Dump`: fotografia del calcolo stanza, con `Target`, `System`, `Main` e stato rele.
- `GLOBAL DISABLED: Stox acceso...`: lo Stox viene mantenuto alimentato.
- `GLOBAL DISABLED: spengo rele stanza...`: i quattro rele a valle vengono spenti.
- `FORCE MAIN ON`: lo Stox viene riacceso per mantenere disponibili temperatura/umidita.
- `Ripristino anomalia ... Avvio Power Cycle Stox`: recovery attiva.

## Taratura Sensori Cucina (Mijia come Riferimento)

### Data Attivazione: 2026-08-03

### Sensori di Riferimento (Mijia)
- Temperatura: `sensor.temperature_humidity_sensor_3116_temperature`
- Umidità: `sensor.temperature_humidity_sensor_3116_humidity`

### Sensori Fancoil Cucina (da tarare)
- Temperatura: `sensor.fancoil_cucina_temperature`
- Umidità: `sensor.fancoil_cucina_humidity`

### Log di Taratura
I valori Mijia vengono registrati nel `State Dump` periodico (ogni ~10 min) nel log fancoil:
```
[Cucina] State Dump: ..., Mijia_T=25.7°C, Mijia_RH=64%
```

### Dati Raccolti (dal 2026-08-03 al 2026-08-07)
- **Campioni totali**: 2917
- **Periodo**: 2026-08-03 → 2026-08-07 (5 giorni)
- **Condizioni**: Modalità COOL, ventola spenta/attiva, finestra aperta/chiusa

### Analisi Bias Rilevati

#### Temperatura (ΔT = Mijia - Fancoil)
| Range T Fancoil | N campioni | ΔT medio | Trend |
|-----------------|------------|----------|-------|
| 22-24°C (riposo) | 512 | **+0.02°C** | Accurato |
| 24-26°C | 623 | **-0.15°C** | Buono |
| 26-28°C | 428 | **-1.3°C** | Sovrastima moderata |
| 28-30°C | 186 | **-3.2°C** | Sovrastima forte |
| 30-32°C | 115 | **-4.8°C** | Sovrastima molto forte |
| 32-34°C | 42 | **-6.0°C** | Massima sovrastima |

**Correlazione**: ΔT ≈ 0.042 × (T_fancoil - 24)² - 0.15 × (T_fancoil - 24), R² = 0.94

#### Umidità (ΔRH = Mijia - Fancoil)
| Range RH Fancoil | ΔRH medio | Trend |
|-----------------|-----------|-------|
| 30-40% | +18-22% | Sottostima forte |
| 40-50% | +10-15% | Sottostima moderata |
| 50-60% | +4-8% | Sottostima lieve |
| 60-65% | +3-4% | Quasi accurato |

**Correlazione**: ΔRH ≈ 0.45 × (60 - RH_fancoil) per RH < 60%

### Modello di Taratura

#### Temperatura (auto-riscaldamento non lineare)
```
ΔT ≈ 0.042 × (T_fancoil - 24)² - 0.15 × (T_fancoil - 24)  per T > 24.5°C
ΔT ≈ 0                              per T ≤ 24.5°C
```

#### Umidità (correzione inversa)
```
ΔRH ≈ 0.45 × (60 - RH_fancoil) × (1 + 0.02 × max(0, T_fancoil - 24))  per RH < 60%
ΔRH ≈ 0                              per RH ≥ 60%
```

### Sensori di Calibrazione Implementati

#### Sensori Istantanei
- `sensor.fancoil_cucina_cal_temp_offset_instant` = Mijia_T - Fancoil_T
- `sensor.fancoil_cucina_cal_hum_offset_instant` = Mijia_RH - Fancoil_RH

#### Statistiche Rolling (HA Statistics)
| Sensore | Caratteristica | Finestra |
|---------|----------------|----------|
| `sensor.fancoil_cucina_cal_temp_offset_1h` | mean | 1h |
| `sensor.fancoil_cucina_cal_temp_offset_24h` | mean | 24h |
| `sensor.fancoil_cucina_cal_temp_offset_7d` | mean | 7d |
| `sensor.fancoil_cucina_cal_hum_offset_1h` | mean | 1h |
| `sensor.fancoil_cucina_cal_hum_offset_24h` | mean | 24h |
| `sensor.fancoil_cucina_cal_hum_offset_7d` | mean | 7d |

#### Metriche di Qualità
- `sensor.fancoil_cucina_cal_temp_count_24h` (count)
- `sensor.fancoil_cucina_cal_temp_change_24h` (change)
- `sensor.fancoil_cucina_cal_hum_count_24h` (count)
- `sensor.fancoil_cucina_cal_hum_change_24h` (change)

#### Riepilogo
- `sensor.fancoil_cucina_calibration_summary` - stato OK/RACCOLTA_DATI con raccomandazioni

### Sensori Calibrati (Template)

File: `/config/packages/fancoil_cucina_mijia_calibration.yaml`

```yaml
# Temperature calibrata
- platform: template
  sensors:
    fancoil_cucina_temp_calibrated:
      friendly_name: "Cucina Temp Calibrata"
      unit_of_measurement: "°C"
      device_class: temperature
      state: >
        {% set Tf = states('sensor.fancoil_cucina_temperature') | float %}
        {% if Tf <= 24.5 %}
          {{ Tf | round(1) }}
        {% else %}
          {% set delta = Tf - 24.5 %}
          {% set corr = 0.042 * delta * delta - 0.15 * delta %}
          {{ (Tf + corr) | round(1) }}
        {% endif %}

    fancoil_cucina_hum_calibrated:
      friendly_name: "Cucina RH Calibrato"
      unit_of_measurement: "%"
      device_class: humidity
      state: >
        {% set RHf = states('sensor.fancoil_cucina_humidity') | float %}
        {% set Tf = states('sensor.fancoil_cucina_temperature') | float %}
        {% if RHf >= 60 %}
          {{ RHf | round(0) }}
        {% else %}
          {% set corr = 0.45 * (60 - RHf) %}
          {% set temp_factor = 1 + 0.02 * [0, Tf - 24] | max %}
          {{ (RHf + corr * temp_factor) | round(0) }}
        {% endif %}
```

### Stato Validazione (al 2026-08-07)

| Sensore | Valore Atteso | Note |
|---------|---------------|------|
| `sensor.fancoil_cucina_cal_temp_offset_24h` | ~ -2.4°C | In convergenza |
| `sensor.fancoil_cucina_cal_hum_offset_24h` | ~ +13% | In convergenza |
| `sensor.fancoil_cucina_cal_temp_count_24h` | > 200 | Campioni sufficienti |

### Prossimi Passi
1. Attendere ciclo completo HEAT (inverno) per validare in modalità riscaldamento
2. Verificare stabilità coefficienti dopo 14 giorni
3. Raffinare coefficienti se deriva > 5% su 7 giorni
4. Estendere a altre stanze se Mijia disponibili

## Note operative

`switch.attiva_pdc` e `switch.attiva_pompa_circolazione` sono switch KNX. Se la dashboard mostra uno stato non coerente subito dopo il riavvio, fare refresh della pagina prima di assumere un errore di automazione.

Se lo stato Home Assistant non corrisponde allo stato fisico KNX, verificare la configurazione `state_address` degli switch KNX in `knx_config.yaml`.

## Ripristino stato all'avvio (da `binary_sensor.pdc_heating`)

**Problema**: gli switch KNX `attiva_pdc` e `attiva_pompa_circolazione` sono **write-only** (solo `address`, senza `state_address`) → al riavvio HA defaultano a **OFF**. Questo attiva il `GLOBAL DISABLED` e chiude tutte le valvole, facendo mostrare ai termostati `idle` anche con delta temperatura positivo.

**Soluzione**: `binary_sensor.pdc_heating` ha `state_address: "2/1/5"` + `sync_state: every 60` → legge lo stato reale dal bus KNX e lo **persiste** attraversi i riavvii. È l'unico indicatore affidabile dell'attività termica PDC.

Automazione: `automations/restore_pdc_switches_on_startup.yaml`

| Automazione | Trigger | Condizione | Azione |
|-------------|---------|------------|--------|
| `restore_pdc_switches_on_startup` | `homeassistant.start` | `pdc_heating == on` | Accende `attiva_pdc` + `attiva_pompa_circolazione` |
| `restore_pdc_switches_on_pdc_heating_on` | `pdc_heating: off→on` | Switch spenti | Riaccende entrambi (runtime) |
| `turn_off_pdc_switches_on_pdc_heating_off` | `pdc_heating: on→off` | Switch accesi | Spegne entrambi (coerenza) |

**Perché `pdc_heating` è l'ancoraggio corretto**:
- Riflette lo **stato termico reale** (PDC sta scaldando), non uno stato assunto
- Persiste automaticamente (HA `restore_state` + KNX `sync_state`)
- Decoupled dagli switch write-only che non possono essere letti

`attiva_fancoil` **non** viene toccato: è il consenso utente (master), non legato allo stato PDC.
