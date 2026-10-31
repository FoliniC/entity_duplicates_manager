# Sistema Esperto di Ottimizzazione Climatica

## Panoramica

Sistema di controllo climatico intelligente per Home Assistant che minimizza l'umidità interna mantenendo i setpoint termostatici, con apprendimento continuo dalle statistiche dei sensori. Architettura a 2 layer: **Layer 1** (consiglio finestra in tempo reale) + **Layer 2** (validazione ex-post dell'efficacia).

---

## Architettura

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT SENSORS                                │
├─────────────────────────────────────────────────────────────────┤
│  Indoor:  T, RH, Omega (assoluta), Trend, Punto di rugiada      │
│  Outdoor: Omega_esterno, T_dew_esterno, Precipitazione, Pioggia │
│  Window:  Contact sensor (KNX/Tuya) o input_boolean manuale     │
│  System:  PDC attiva, Pompa circolazione, Fancoil, Setpoint     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: WINDOW ADVICE                       │
│  (sensor.consiglio_finestra_<stanza>)                          │
├─────────────────────────────────────────────────────────────────┤
│  • Algoritmo adattivo basato su Δω (g/kg) + calo_RH_previsto    │
│  • Nessuna soglia RH fissa (rimossa soglia 58%)                 │
│  • Valutazione costo termico: ΔT, setpoint, rapporto beneficio  │
│  • Grace period 5 min, isteresi 10 min, trend umidità          │
│  • Output: apri | chiudi | mantieni_aperta | mantieni_chiusa   │
│  • Debounce 5 min → binary_sensor.consiglio_finestra_<stanza>_d│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: VALIDATION                          │
│  (sensor.esito_ultimo_consiglio_finestra_<stanza>_validated_v3)│
├─────────────────────────────────────────────────────────────────┤
│  • State machine: in_attesa → in_corso → efficace/inefficace   │
│  • Verdetto a 15 min POST-chiusura (non 60 min da apertura)    │
│  • Cattura ω/RH a 15/30/60 min post-chiusura                   │
│  • Persistenza sessione via attributi (chiusa_ts, n_riaperture)│
│  • Single nxt JSON variable (no namespace isolation issues)    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PREDICTION ENGINE                            │
│  (sensor.previsione_finestra_<stanza>)                         │
├─────────────────────────────────────────────────────────────────┤
│  • Modello fisico: τ per stanza (camera_grande=14, cucina=3)   │
│  • Conversione ω→RH fisica: 100/ω_sat(T) ≈ 6.8-7.2 pp per g/kg │
│  • Bias correction: -7.3 pp (calibrato su aperture reali)      │
│  • Output: predicted_humidity, humidity_delta_predicted        │
│  • Horizon: input_number.previsione_orizzonte_minuti (default 15)│
└─────────────────────────────────────────────────────────────────┘
```

---

## Stanze Configurate

| Stanza | ID | Finestra | Setpoint | τ (min) | Sensore Contatto |
|--------|-----|----------|----------|---------|------------------|
| Cucina | `cucina` | Sì | 20.0°C | 3.0 | `binary_sensor.contact_cucina_contact_cucina` |
| Camera Grande | `camera_grande` | Sì | **21.5°C** | **14.0** | `binary_sensor.finestra_camera_grande_finestra_camera_grande` |
| Camera | `camera` | Sì | 20.0°C | 4.0 | `input_boolean.finestra_camera_aperta` |
| Bagno | `bagno` | Sì | 21.0°C | 3.0 | `input_boolean.finestra_bagno_aperta` |
| Sala | `sala` | Sì | 20.0°C | 4.0 | `input_boolean.finestra_sala_aperta` |
| Corridoio | `corridoio` | **No** (porte) | 20.0°C | 4.0 | N/A |

---

## Layer 1: Algoritmo Consiglio Finestra

### Variabili Chiave

```yaml
# Umidità assoluta interna ed esterna (g/kg)
omega_int, omega_esterno

# Delta assoluto: quanto più secco è l'esterno
delta_omega = omega_int - omega_esterno

# Calo RH previsto se apriamo (da prediction sensor)
calo_umidita_previsto = RH_attuale - predicted_humidity

# Temperatura
t_int, t_ext, t_setpoint (da climate entity)
delta_t = t_int - t_ext
calo_temp_previsto = delta_t * exchange_fraction (≈0.3)
rapporto_beneficio_costo = calo_umidita_previsto / calo_temp_previsto (pp/°C)
```

### Albero Decisionale (Finestra CHIUSA)

```jinja2
{% if not valid_data %}incerto
{% elif rain %}chiudi                    # Pioggia → mai aprire
{% elif not has_window %}apri_porte_ricambio  # Solo porte (corridoio)
{% elif system_active %}                 # Impianto ATTIVO (soglie alte)
    {% if delta >= 2.0 and rh_drop >= 5.0 %}apri
    {% elif delta >= 1.5 and rh_drop >= 4.0 %}apri_se_riparata
    {% else %}mantieni_chiusa
{% else %}                               # Impianto SPENTO (soglie basse)
    {% if delta >= 1.5 and rh_drop >= 4.0 %}apri
    {% elif delta >= 1.0 and rh_drop >= 3.0 %}apri_se_riparata
    {% else %}mantieni_chiusa
{% endif %}
```

### Albero Decisionale (Finestra APERTA) — **Ordine Critico**

```jinja2
{% if rain %}chiudi                          # 1. Pioggia: chiudi SUBITO
{% elif minuti < 5 %}mantieni_aperta         # 2. Grace period 5 min
{% elif trend == 'in_salita' %}chiudi        # 3. Umidità RISALE: chiudi SUBITO (ricambio fallito)
{% elif trend == 'stabile' and minuti >= 10 %}chiudi  # 4. Stabile 10 min: scambio esaurito
{% elif dT > 8 and rh_drop < 6 %}chiudi      # 5. Freddo fuori + beneficio modesto: risparmia calore
{% elif rbc > 0 and rbc < 2 and dT > 5 %}chiudi # 6. Rapporto beneficio/costo < 2 pp/°C
{% elif t_int < t_setpoint and dT > 3 %}chiudi  # 7. Sotto setpoint + perdita calore
{% elif azione_raw_prec == 'mantieni_aperta' and (now - mantieni_da) < 600 %}mantieni_aperta  # 8. Isteresi 10 min
{% elif trend == 'in_calata' and (rh_drop >= calo_min or delta >= delta_min) and minuti < 20 %}mantieni_aperta
{% elif delta < delta_min_mantenimento %}chiudi
{% elif rh_drop < calo_min_mantenimento %}chiudi
{% elif trend == 'stabile' and rh < 55 %}chiudi
{% elif trend == 'stabile' and minuti >= 15 %}chiudi
{% elif trend in ['incerto'] and delta >= delta_min and rh_drop >= calo_min and minuti < 25 %}mantieni_aperta
{% else %}chiudi
```

### Soglie Adattive

| Modalità | Δω apertura | RH drop apertura | Δω mantenimento | RH drop mantenimento |
|----------|-------------|------------------|-----------------|----------------------|
| Sistema SPENTO | ≥ 1.5 g/kg | ≥ 4.0 pp | ≥ 1.0 g/kg | ≥ 2.0 pp |
| Sistema ATTIVO | ≥ 2.0 g/kg | ≥ 5.0 pp | ≥ 1.5 g/kg | ≥ 2.0 pp |

### Logica Costo Termico (Nuova)

Per **camera_grande** (setpoint 21.5°C):
- Se `delta_t > 8°C` (es. 21.5 interno, 13.5 esterno) **E** `rh_drop < 6 pp` → **chiudi** (non vale la pena disperdere calore)
- Se `rapporto_beneficio_costo < 2 pp/°C` **E** `delta_t > 5°C` → **chiudi**
- Se `t_int < t_setpoint` **E** `delta_t > 3°C` → **chiudi** (sotto setpoint, non raffreddare ulteriormente)

---

## Layer 2: Validazione Efficacia

### State Machine

```
in_attesa  → (consiglio apri/chiudi + finestra cambia) → in_corso
in_corso   → (finestra chiusa + 15 min trascorsi)      → efficace / inefficace / non_valutabile
```

### Criteri Verdetto (a 15 min post-chiusura)

| Esito | Condizione |
|-------|------------|
| **efficace** | Δω_15m ≥ 0.5 g/kg **E** ΔRH_15m ≤ -2 pp |
| **inefficace** | Δω_15m < 0.2 g/kg **O** ΔRH_15m ≥ 0 pp |
| **non_valutabile** | Dati mancanti, finestra riaperta, durata < 3 min |

### Attributi Salvati

```yaml
tipo_azione: "apri" | "chiudi"
umidita_inizio, umidita_15m, umidita_30m, umidita_60m
omega_inizio, omega_15m, omega_30m, omega_60m
delta_omega_15m, delta_omega_30m, delta_omega_60m
delta_umidita_15m, delta_umidita_30m, delta_umidita_60m
motivo: "testo esplicativo"
chiusa_ts: timestamp chiusura finestra
n_riaperture: conteggio riaperture durante sessione
```

---

## Prediction Engine

### Modello Fisico

```
RH(t) = RH_esterno + (RH_interno - RH_esterno) * exp(-t/τ)
ω(t)  = ω_esterno  + (ω_interno  - ω_esterno)  * exp(-t/τ)
```

### Parametri Per Stanza

| Stanza | τ (min) | Note |
|--------|---------|------|
| camera_grande | **14.0** | Volume grande, ricambio lento (3 aperture reali) |
| cucina | 3.0 | Volume piccolo, ricambio veloce |
| bagno | 3.0 | Volume piccolo, estrazione forzata |
| camera, sala, corridoio | 4.0 | Default |

### Correzione Bias

- **Bias RH**: -7.3 pp (predizione sovrastimava RH finale → correzione negativa)
- Applicata su `calo_previsto_rh` prima di confronto con soglie

### Output Espositi

```yaml
predicted_humidity: 44.5      # RH finale previsto (%)
humidity_delta_predicted: -18.5  # Delta RH previsto (pp)
tempo_utile_min: 8
rh_finale_previsto: 44.5
omega_finale_previsto: 6.2
confidence: 72
horizon_used: 15
bias_applied: -7.3
```

---

## Sensori Derivati

### Trend Umidità (`sensor.trend_umidita_<stanza>`)

Basato su `statistics_umidita_*_change_breve/medio` (15m/60m):
- `in_salita`: cb ≥ 0.5 o (cb ≥ 0.2 e cm ≥ 1.0)
- `in_calata`: cb ≤ -0.5 o (cb ≤ -0.2 e cm ≤ -1.0)
- `stabile`: |cb| ≤ 0.3 e |cm| ≤ 0.6
- `incerto`: altrimenti

### Omega Esterno (`sensor.omega_esterno`)

Filtro outlier su `clima_locale` (priorità) e `meteo_locale` (fallback):
- Validazione: 5°C ≤ T ≤ 45°C, 10% ≤ RH ≤ 100%
- Se outlier → `this.state` (ultimo valore valido)
- Attributi: `temperatura`, `punto_di_rugiada_esterno`

### Umidità Pilota (`sensor.umidita_<stanza>_pilota`)

Fallback chain: Fancoil → Tuya TH → `input_number.umidita_<stanza>_ultima_valida`

---

## Automazioni Chiave

| Automazione | Trigger | Azione |
|-------------|---------|--------|
| `*_memorizza_umidita_valida` | RH valido + finestra chiusa | Salva in `input_number.umidita_<stanza>_ultima_valida` |
| `*_reset_stuck_session` | Ogni 5 min | Force update se `validated_v3` in `in_attesa` > 15 min |
| `*_verification` | Contatto finestra cambia | Log analytics + outcome evaluation |
| `*_window_notification` | Consiglio stabile 5 min | Persistent notification |
| `*_window_logger` | Consiglio/finestra cambia | Event log `fancoil_events.log` |

---

## Persistenze (Sopravvivono a Riavvio)

| File | Entità | Scopo |
|------|--------|-------|
| `*_persistence.yaml` | `sensor.temperatura_<stanza>_reale_calcolata` | History sorgenti temperatura |
| `th_persistence.yaml` | `sensor.th1a_*`, `th2b_*`, `th3c_*`, `th4d_*` | Tuya TH sensori + batteria |
| `master_persistence.yaml` | `sensor.fancoil_system_saved_hvac_mode` | Ripristino modalità HVAC master |
| `ev_persistence.yaml` | `sensor.ev_charge_2025_saved_*` | Impostazioni ricarica EV |
| `consumo_netto_pdc_persistence.yaml` | `sensor.smart_meter_2026_a_pdc_power_a` | Potenza PDC |

---

## File Generati (Struttura)

```
yaml_generator/
├── templates/                    # Template Jinja2 + %%PLACEHOLDER%%
│   ├── fancoil_window_advice.j2      # Layer 1 algorithm
│   ├── fancoil_window_efficiency.j2  # Layer 2 validation
│   ├── fancoil_prediction_sensor.j2  # Prediction engine
│   ├── fancoil_verification_mode.j2  # Analytics automation
│   ├── fancoil_binary_sensor_debounced_advice.j2
│   ├── fancoil_manual_advice.j2
│   ├── fancoil_climate.j2
│   ├── fancoil_coherence_sensors.j2
│   └── ... (altri template)
├── managed_trigger_sensors/      # Trigger-based template sensors
│   ├── <stanza>_window_advice.yaml
│   ├── <stanza>_window_efficiency.yaml
│   ├── <stanza>_prediction.yaml
│   ├── <stanza>_climate_advice.yaml
│   ├── <stanza>_window_logger.yaml
│   └── <stanza>_manual_advice.yaml
├── managed_binary_sensors/       # Binary sensors (legacy + debounced)
├── managed_sensors/              # Template sensors (legacy)
├── managed_persistence/          # Trigger-based persistence
├── generated_climates/           # climate_template entities
├── automations/                  # Tutte le automazioni
└── fancoil_templates_master.yaml # Master include per HA
```

---

## Generazione & Deploy

```bash
cd /home/carlo/docker/homeassistant/config
python3 yaml_generator/generate_fancoil_climates.py
python3 yaml_generator/lint_template_sensors.py yaml_generator/managed_trigger_sensors/
docker stop homeassistant && sleep 5 && docker start homeassistant
```

### Convenzioni Template

- `%%PLACEHOLDER%%` → sostituzione Python (valori stanza)
- `{{...}}` / `{%...%}` → logica Jinja2 runtime HA
- Trigger-based template sensors **obbligatori** (HA 2023+)
- Single `nxt` JSON variable per state machine complessi (evita namespace isolation)
- `from_json(default={...})` per estrazione attributi sicura
- Double-quoted Jinja strings per testo con apostrofi (`motivo="..."`)

---

## Diagnostica

### Query DB (MariaDB)

```bash
docker exec homeassistant python3 /config/ha_clima_diagnostica.py \
  --since 1h \
  --out /config/report.md \
  --db "mariadb+pymysql://homeassistant:***@192.168.0.3:3306/homeassistant"
```

### Log Eventi

```bash
tail -f /home/carlo/docker/homeassistant/config/logs/fancoil_events/fancoil_events.log
```

### Verifica Entità Chiave

```bash
# Prediction sensors (6 stanze)
ha sensor list | grep previsione_finestra

# Layer 2 validated (5 stanze con finestra)
ha sensor list | grep validated_v3

# Window advice
ha sensor list | grep consiglio_finestra
```

---

## Problemi Risolti (Storico)

| Issue | Fix |
|-------|-----|
| TemplateSyntaxError `ns['k']` | Single `nxt` JSON variable |
| Debounce false triggers (16/h) | `primo_avvio = states(self) in ['unknown',...]` |
| "longer than 255" log spam | Attributes at same level as state (not folded scalar) |
| Ghost sensors after restart | Unique_id change + full container stop/start |
| Prediction sensors missing attributes | v5 template: espone `predicted_humidity`, `humidity_delta_predicted` |
| RH threshold 58% bloccava camera_grande | `>= 58.0` + per-room τ |
| Premature chiudi after open | Grace period 5 min + `in_salita` before hysteresis |
| Verification/dashboard lag | Read raw `candidato` attribute (not debounced state) |
| Hysteresis blocked `in_salita` | Moved `in_salita` check **before** hysteresis |
| Master YAML invalid | All entries as list items (`- ` prefix) |

---

## Prossimi Sviluppi

- [ ] Calibrazione τ per stanza su aperture reali (≥10 campioni)
- [ ] Integrazione previsioni meteo (probabilità pioggia > 50% → preventivo chiudi)
- [ ] Auto-tuning soglie Δω/RH drop per stanza via Layer 2 outcomes
- [ ] Dashboard analitica efficacia per stagione
- [ ] Notifica proattiva: "Tra 30 min conviene aprire" (basato su trend + meteo)

---

## Referenze

- `TELECAMERE.md`, `RETE_LOCALE.md` — vincoli rete/routing (non alterare senza consenso)
- `ha_clima_diagnostica.py` — diagnostica DB recorder
- `analyze_fancoil_log.py` — analisi `fancoil_events.log`
- `lint_template_sensors.py` — validazione struttura YAML generata