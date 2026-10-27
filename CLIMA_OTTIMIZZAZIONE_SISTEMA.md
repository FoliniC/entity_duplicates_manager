# Sistema di Ottimizzazione del Clima (Climate Optimization System)

## Obiettivo Principale

Minimizzare l'umidità relativa dell'appartamento **mantenendo la temperatura impostata dai termostati**, attraverso un **sistema esperto** che genera consigli apertura/chiusura finestre e impara dai risultati per migliorare progressivamente l'accuratezza.

---

## Architettura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INPUT SENSORI (Per Stanza)                       │
├──────────────────┬──────────────────┬──────────────────────────────┤
│ Interni          │ Esterni          │ Stato Impianto               │
│ • T_int (pilota) │ • Omega_esterno  │ • hvac_action (climate)      │
│ • RH_int (pilota)│ • T_esterno      │ • switch fancoil (1-4)       │
│ • RH_fallback    │ • RH_esterno     │ • PDC/pompa/fancoil global   │
│ • RH_KNX (TH)    │ • Precipitazioni │ • deumidificazione attiva    │
│ • Trend RH       │                  │                              │
└──────────────────┴──────────────────┴──────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LAYER 1: CONSIGLIO FINESTRA                        │
│  sensor.consiglio_finestra_<stanza> (trigger-based, 1 min)         │
│  Decision tree basato su:                                           │
│  • Delta Omega (ω_int - ω_ext) = potenziale deumidificazione       │
│  • Previsione calo umidità (sensor.previsione_finestra_<stanza>)   │
│  • Trend umidità interna (in_salita/in_calata/stabile/incerto)     │
│  • Stato finestra (contact sensor o input_boolean)                 │
│  • Impianto attivo (riscaldamento/raffreddamento/deumidificazione) │
│  • Pioggia esterna                                                  │
│  • Minuti finestra aperta                                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LAYER 2: VALUTAZIONE ESPERTA (Efficiency)          │
│  sensor.esito_ultimo_consiglio_finestra_<stanza>_validated         │
│  Valida l'efficacia dell'azione eseguita:                           │
│  • Apertura finestra → RH deve scendere ≥ 2% in 60 min             │
│  • Chiusura finestra → RH deve restare stabile (Δ ≤ 0.4%)          │
│  Controlli qualità dati:                                            │
│  - Validità range sensori (0-100%)                                  │
│  - Transition Rate (max %/min fisiologici)                          │
│  - Coerenza multi-sensore (Pilota vs TH vs Esterno)                 │
│  - Data freshness (< 60 min)                                        │
│  - Trend validation                                                 │
│  Esiti: efficace / inefficace / non_valutabile / in_attesa         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  LAYER 3: ANALYTICS & TUNING                        │
│  sensor.analytics_tuning_<stanza>                                   │
│  Metriche aggregate:                                                │
│  • Override Rate (% volte utente ha ignorato il consiglio)         │
│  • Accuracy (% consigli risultati efficaci)                         │
│  • Log azioni manuali con outcome                                   │
│  • Confidenza consiglio (basata su storia + qualità dati)           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  FEEDBACK LOOP (Apprendimento)                      │
│  • Regole fisse → Soglie adattive per stanza                       │
│  • Pesi variabili per Delta Omega, Trend, Tempo apertura           │
│  • Penalità confidenza se azione manuale contraria                 │
│  • Boost confidenza se esito = efficace                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Variabili Chiave per Stanza

| Variabile | Fonte | Descrizione |
|-----------|-------|-------------|
| `t_int` | `sensor.temperatura_<stanza>_reale_calcolata` (fallback fancoil) | Temperatura interna °C |
| `rh_int` | `sensor.umidita_<stanza>_pilota` (fallback fancoil/KNX/esterno) | Umidità interna % |
| `omega_int` | `sensor.omega_<stanza>` | Rapporto di miscela interno g/kg |
| `omega_ext` | `sensor.omega_esterno` | Rapporto di miscela esterno g/kg |
| `delta_omega` | Calcolato | `omega_int - omega_ext` (potenziale deumidificazione) |
| `trend` | `sensor.trend_umidita_<stanza>` | `in_salita` / `in_calata` / `stabile` / `incerto` |
| `finestra_aperta` | Contact sensor / `input_boolean` | Stato fisico finestra |
| `minuti_aperta` | Calcolato da `last_changed` | Durata apertura corrente |
| `fancoil_attivo` | Switch velocità 1-4 | Ventilazione forzata attiva |
| `impianto_attivo` | Climate hvac_action + switch | Termoregolazione attiva |
| `piove` | `sensor.castionetto_precipitazione` > 0 | Blocco apertura per pioggia |

---

## Albero Decisionale (Consiglio Finestra)

### Finestra CHIUSA → Valuta APERTURA

```
IF dati_non_validi          → "incerto"
ELSE IF no_finestra         → "apri_porte_ricambio"  (se delta_omega≥1.5 E calo_previsto≥4% E RH>58%)
                              "chiudi_porte"          (se delta_omega<0.2)
                              "nessuna_azione"
ELSE IF delta_omega ≥ 2.5 
     AND calo_previsto ≥ 6%
     AND RH > 62%
     AND NOT piove         → "apri" (forte potenziale)
ELSE IF delta_omega ≥ 1.5 
     AND calo_previsto ≥ 4%
     AND RH > 58%
     AND NOT piove         → "apri_se_riparata" (potenziale moderato)
ELSE                        → "nessuna_azione"
```

### Finestra APERTA → Valuta CHIUSURA

```
IF piove                          → "chiudi" (priorità sicurezza)
ELSE IF trend == 'in_salita'      → "chiudi" (peggiora)
ELSE IF impianto_attivo AND min≥8 → "chiudi" (dispersione energia)
ELSE IF impianto_attivo AND min≥5 AND NOT (trend favorevole forte) → "chiudi"
ELSE IF delta_omega < 0.2         → "chiudi" (nessun vantaggio)
ELSE IF RH ≤ 55%                  → "chiudi" (target raggiunto)
ELSE IF trend == 'stabile' AND min≥12 → "chiudi" (diminuendo returns)
ELSE IF calo_previsto < 2%        → "chiudi" (marginale)
ELSE                              → "mantieni_aperta"
```

---

## Sistema di Validazione Qualità Dati (Layer 2)

### 4 Livelli di Controllo

| Check | Descrizione | Soglia | Azione se Fallisce |
|-------|-------------|--------|-------------------|
| **Range Validity** | RH in [0, 100] | - | Marca sensore invalido, usa fallback |
| **Transition Rate** | Variazione %/min fisiologica | Apertura: 30%/15min, 50%/30min, 80%/60min<br>Chiusura: 20%/15min, 35%/30min, 50%/60min | Marca `non_valutabile` |
| **Coerenza Multi-sensore** | Pilota vs TH vs Esterno | Δ Pilota-TH ≤ 15%, Δ Pilota-Esterno ≤ 20% | Usa fallback, segna `coerenza_sensori_non_aggressivi` |
| **Data Freshness** | Ultimo aggiornamento < 60 min | - | Marca `dati_troppo_vecchi`, `non_valutabile` |

### Gerarchia Fallback Umidità

1. **Primario**: `sensor.umidita_<stanza>_pilota` (fancoil calibrato)
2. **Secondario**: `sensor.th<X>_humidity` (Tuya TH stanza)
3. **Terziario**: `sensor.meteo_castionetto_umidita` (esterno)

---

## Metriche di Apprendimento (Layer 3)

### `sensor.analytics_tuning_<stanza>`

| Metrica | Calcolo | Utilizzo |
|---------|---------|----------|
| `override_rate` | `azioni_manuali_contrarie / consigli_totali` | Penalizza confidenza se > 30% |
| `consiglio_accuracy` | `esiti_efficaci / esiti_valutabili` | Boost confidenza se > 70% |
| `confidenza` | Base (50%) ± history ± qualità dati | Peso decisionale albero |

### Log Azioni Manuali

`input_button.log_azione_manuale_<stanza>` registra:
- Azione: `apertura_finestra` / `chiusura_finestra` / `apertura_porte` / `chiusura_porte`
- Timestamp
- Stato sistema al momento (RH, delta_omega, trend, impianto)
- Esito successivo (efficace/inefficace) → **ground truth per training**

---

## Stato Attuale per Stanza (2026-10-25)

| Stanza | Contact Sensor | Input Boolean | Fallback RH | Note |
|--------|----------------|---------------|-------------|------|
| **Cucina** | `binary_sensor.contact_cucina_contact_cucina` | ❌ Non creato | TH1A | Auto |
| **Camera Grande** | `binary_sensor.finestra_camera_grande_finestra_camera_grande` | ❌ Non creato | TH2B | Auto |
| **Camera** | ❌ | ✅ `finestra_camera_aperta` | TH3C | Manuale |
| **Bagno** | ❌ | ✅ `finestra_bagno_aperta` | Fancoil | Manuale |
| **Sala** | ❌ | ✅ `finestra_sala_aperta` | Fancoil | Manuale |
| **Corridoio** | N/A (no finestra) | ❌ `has_window: false` | Fancoil | Solo porte |

---

## Configurazione Soglie (Input Number Globali)

```yaml
input_number:
  fan_distance_high:      2.0   # ΔT per HIGH
  fan_distance_medium:    1.2   # ΔT per MEDIUM
  fan_distance_low:       0.5   # ΔT per LOW
  fan_distance_idle:      0.3   # ΔT per IDLE (valvola sola)
  fan_distance_stop:     -0.3   # ΔT per STOP
  fan_distance_resume:    0.5   # Isteresi ripresa
  fancoil_resume_delay_minutes: 3
  
  # Soglie finestra (da fancoil_vars.yaml per stanza)
  verifica_thresholds:
    delta_omega_apertura:  1.5  # g/kg min per consiglio apri
    delta_omega_chiusura:  0.3  # g/kg max per consiglio chiudi
    confidence_penalty_active_fancoil: -25  # Penalità se fancoil attivo
```

---

## Metodi di Miglioramento Futuri

### 1. **Soglie Adattive per Stanza (Bayesian Bandit)**
- Sostituire soglie fisse (`delta_omega_apertura: 1.5`) con distribuzioni posteriori per stanza
- Thompson Sampling: esplora/esplora automaticamente la soglia ottimale
- Aggiorna `alpha/beta` ad ogni outcome (efficace/inefficace)

### 2. **Modello Predittivo ML (LightGBM / XGBoost on-edge)**
- Features: `T_int, RH_int, T_ext, RH_ext, delta_omega, trend, ora_giorno, stagione, impianto_attivo, minuti_aperti`
- Target: `delta_RH_60min` (regressione) o `efficace` (classificazione)
- Training incrementale su storico `esito_ultimo_consiglio` + `log_attivita_manuali`
- Deploy: Home Assistant `pyscript` o container sidecar (`scikit-learn` + `joblib`)

### 3. **Ottimizzazione Multi-Obiettivo (Pareto)**
- Obiettivi: Minimizza RH, Minimizza dispersione termica, Mantieni comfort (PMV/PPD)
- Variabili decisionali: `apri/chiudi` + `durata_apertura` + `velocità_fancoil`
- Algoritmo: NSGA-II o semplice weighted sum con pesi appresi

### 4. **Transfer Learning tra Stanze**
- Stanza con molti dati (Cucina) → pre-addestra modello
- Fine-tune su stanze con pochi dati (Camera, Bagno)
- Condividi embedding `stanza → parametri_tipo` (es. `volume_m3, esposizione, infissi`)

### 5. **Integrazione Previsione Meteo (3-24h)**
- Usa `sensor.meteo_castionetto_*` forecast per pianificare aperture anticipate
- Es: "Domani pioggia → chiudi stasera, accumula calore"
- Es: "Vento secco domani → apri stanotte per pre-deumidificare"

### 6. **Calibrazione Continua Sensori (Drift Detection)**
- CUSUM / Page-Hinkley su residui `Pilota - TH` / `Pilota - Esterno`
- Auto-trigger ricalibrazione `fancoil_cucina_mijia_calibration.yaml` coefficients
- Alert se drift > 2% su 7 giorni

### 7. **Digital Twin Termico per Stanza**
- Modello RC (Resistance-Capacitance) per stanza: `C * dT/dt = (T_ext - T_int)/R + Q_int + Q_fancoil`
- Parametri `R, C` identificati da dati storico (system identification)
- Simula "what-if" prima di dare consiglio: "Se apro 15min, T scende 0.8°C, RH scende 4%"

### 8. **Gamification / UX Feedback**
- Dashboard "Score Settimanale": % consigli seguiti, % efficaci, litri acqua risparmiati (deumidificatore)
- Notifica push solo se confidenza > 80% E impatto stimato > soglia
- Modalità "Auto-pilot" (esegue consigli senza conferma) per stanze ad alta accuracy

---

## File di Riferimento

| Componente | Path Template | Output Generato |
|------------|---------------|-----------------|
| Consiglio Finestra | `templates/fancoil_window_advice.j2` | `managed_trigger_sensors/*_window_advice.yaml` |
| Previsione Finestra | `templates/fancoil_window_efficiency.j2` | `managed_trigger_sensors/*_window_efficiency.yaml` |
| Valutazione Esito | `templates/fancoil_window_efficiency_v2.j2` | `automations/*_verification.yaml` |
| Analytics Tuning | `templates/fancoil_analytics_tuning.j2` | `managed_sensors/*_analytics.yaml` |
| Dashboard | `templates/dashboard_main.j2` + `dashboard_room_details.j2` | `ui/riscaldamento.yaml` |
| Config Stanze | `yaml_generator/fancoil_vars.yaml` | - |

---

## Persistenza Dati Decisionali e Sample (per Valutazione Qualità)

### Template Sensors HA (Storage Primario)

Tutti i dati decisionali, outcome e sample di training risiedono in **template sensors trigger-based** che:
- Persistono via HA `core.restore_state` (riavvio)
- Vengono storicizzati da `recorder` su **MariaDB** (tabelle `states`, `state_attributes`)
- Espongono attributi JSON ricchi per query SQL / ML offline

| Sensor (per stanza) | Ruolo | Attributi Chiave per Training/Valutazione |
|---------------------|-------|-------------------------------------------|
| `sensor.log_attivita_manuali_<stanza>` | **Ground truth azioni utente** | `action_count`, `override_count`, `concordant_count`, `last_action`, `last_recommendation`, `last_window_before`, `last_window_after`, `user_id_last`, `timestamp_last` |
| `sensor.esito_ultimo_consiglio_finestra_<stanza>_validated` | **Outcome efficacia** (label) | `state` ∈ {efficace, inefficace, non_valutabile, in_attesa}, `umidita_inizio`, `ora_inizio_valutazione`, `tipo_azione` (apertura/chiusura), `esito_15m/30m/60m`, `dati_primari_validi`, `controllo_coerenza_superato`, `eta_dati_minuti`, `trend_valido`, `note_validazione`, `sensore_fallback_usato`, `affidabilita_dati_pct`, `coerenza_sensori_pct` |
| `sensor.analytics_tuning_<stanza>` | **Metriche aggregate learning** | `override_rate` (%), `consiglio_accuracy` (%), `optimal_thresholds` (JSON), `prediction_factor_humidity/temperature/time`, `prediction_count`, `prediction_ok_count`, `prediction_accuracy`, `pattern_analysis` (JSON) |
| `sensor.previsione_finestra_<stanza>` | **Previsioni + parametri modello** | `horizon_minutes`, `predicted_humidity`, `predicted_temperature`, `delta_omega`, `exchange_fraction`, `prediction_factor_*`, `external_source/temperature/humidity`, `hvac_mode`, `hvac_setpoint`, `hvac_active_for_prediction` |
| `sensor.consiglio_manuale_<stanza>` | **Override manuali** (training label) | `consiglio_originale`, `manuale_assegnato`, `motivo`, `azione_utente` (open_15m/close_5m/pause/reset), `utente_id`, `timestamp`, `finestra_prima`, `finestra_dopo`, `fancoil_attivo` |

### Storage Fisico (MariaDB)

```sql
-- Tabelle recorder principali
MariaDB [homeassistant]> DESCRIBE states;
+------------------+--------------+------+-----+---------+----------------+
| Field            | Type         | Null | Key | Default | Extra          |
+------------------+--------------+------+-----+---------+----------------+
| state_id         | bigint       | NO   | PRI | NULL    | auto_increment |
| entity_id        | varchar(255) | NO   | MUL | NULL    |                |
| state            | varchar(255) | YES  |     | NULL    |                |
| attributes_id    | bigint       | YES  | MUL | NULL    |                |
| event_id         | bigint       | YES  | MUL | NULL    |                |
| last_changed_ts  | datetime(6)  | NO   | MUL | NULL    |                |
| last_updated_ts  | datetime(6)  | NO   |     | NULL    |                |
| old_state_id     | bigint       | YES  | MUL | NULL    |                |
+------------------+--------------+------+-----+---------+----------------+

MariaDB [homeassistant]> DESCRIBE state_attributes;
+----------------+----------+------+-----+---------+----------------+
| Field          | Type     | Null | Key | Default | Extra          |
+----------------+----------+------+-----+---------+----------------+
| attributes_id  | bigint   | NO   | PRI | NULL    | auto_increment |
| shared_attrs   | longtext | YES  |     | NULL    |                |
+----------------+----------+------+-----+---------+----------------+
-- shared_attrs contiene JSON con tutti gli attributi sopra
```

### Query Esempio: Training Set per ML (30 giorni)

```sql
-- Campioni etichettati: (features al momento consiglio) → (esito a 60min)
SELECT 
  s.entity_id as stanza,
  s.last_changed_ts as ts_consiglio,
  s.state as consiglio_sistema,
  sa.attributes->>'$.azione_utente' as azione_utente,
  sa.attributes->>'$.finestra_prima' as finestra_prima,
  sa.attributes->>'$.finestra_dopo' as finestra_dopo,
  sa.attributes->>'$.fancoil_attivo' as fancoil_attivo,
  sa.attributes->>'$.timestamp' as ts_azione,
  -- Features contestuali (da joinare con states storico)
  e.state as esito_finale,
  e.attributes->>'$.umidita_inizio' as rh_inizio,
  e.attributes->>'$.delta_omega' as delta_omega,
  e.attributes->>'$.affidabilita_dati_pct' as data_quality_pct,
  e.attributes->>'$.controllo_coerenza_superato' as coherence_ok,
  e.attributes->>'$.sensore_fallback_usato' as fallback_used
FROM states s
JOIN state_attributes sa ON s.attributes_id = sa.attributes_id
LEFT JOIN states e ON e.entity_id = CONCAT('sensor.esito_ultimo_consiglio_finestra_', 
    REPLACE(SUBSTRING_INDEX(s.entity_id, '_', -1), 'manuale', ''), '_validated')
    AND e.last_changed_ts > s.last_changed_ts
    AND e.last_changed_ts <= DATE_ADD(s.last_changed_ts, INTERVAL 90 MINUTE)
WHERE s.entity_id LIKE 'sensor.consiglio_manuale_%'
  AND s.last_changed_ts > DATE_SUB(NOW(), INTERVAL 30 DAY)
  AND e.state IN ('efficace', 'inefficace')
ORDER BY s.last_changed_ts;
```

### Export per ML Offline (Python/Pandas)

```python
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://homeassistant:***@192.168.0.3:3306/homeassistant")

query = """
SELECT 
  s.entity_id, s.state, s.last_changed_ts,
  JSON_EXTRACT(sa.shared_attrs, '$.azione_utente') as azione_utente,
  JSON_EXTRACT(sa.shared_attrs, '$.finestra_prima') as finestra_prima,
  JSON_EXTRACT(sa.shared_attrs, '$.delta_omega') as delta_omega,
  JSON_EXTRACT(ea.shared_attrs, '$.esito') as esito,
  JSON_EXTRACT(ea.shared_attrs, '$.umidita_inizio') as rh_inizio,
  JSON_EXTRACT(ea.shared_attrs, '$.affidabilita_dati_pct') as quality_pct
FROM states s
JOIN state_attributes sa ON s.attributes_id = sa.attributes_id
LEFT JOIN states e ON e.entity_id = REPLACE(s.entity_id, 'consiglio_manuale', 'esito_ultimo_consiglio_finestra')
    AND e.last_changed_ts BETWEEN s.last_changed_ts AND DATE_ADD(s.last_changed_ts, INTERVAL 90 MINUTE)
LEFT JOIN state_attributes ea ON e.attributes_id = ea.attributes_id
WHERE s.entity_id LIKE 'sensor.consiglio_manuale_%'
  AND s.last_changed_ts > DATE_SUB(NOW(), INTERVAL 60 DAY)
  AND e.state IN ('efficace', 'inefficace')
"""

df = pd.read_sql(query, engine)
df.to_parquet("training_samples.parquet")  # Pronto per LightGBM/XGBoost
```

### Persistenza Cross-Restart

| Meccanismo | Cosa Protegge |
|------------|---------------|
| `trigger: platform: homeassistant, event: start` (su tutti i template sensors) | Ripristino stato `state` + `attributes` da `core.restore_state` |
| `recorder` (MariaDB, `purge_keep_days: 10`) | History completa per training, trend, analytics |
| `sync_state: every 60` (KNX binary_sensor) | Stato fisico finestra/PDC persistito su bus |

---

## Note Operative

1. **Riavvio HA**: Tutti i sensori trigger-based hanno `platform: homeassistant, event: start` → riprendono subito
2. **Dati mancanti**: Sistema degrada graziosamente (fallback sensori, `incerto` se nessun dato)
3. **Override utente**: `input_boolean.verifica_mode` disabilita automazioni, logga azioni manuali per training
4. **Debug**: `sensor.analytics_tuning_<stanza>` mostra override_rate, accuracy, ultima azione manuale
5. **Storicizzazione**: Tutti gli esiti finiscono in `sensor.log_attivita_manuali_<stanza>` (attributes JSON) → esportabile per ML offline

---

*Documento generato dall'analisi dei template `yaml_generator/templates/fancoil_window_advice.j2`, `fancoil_window_efficiency*.j2`, `fancoil_analytics_tuning.j2` e configurazione `fancoil_vars.yaml`*