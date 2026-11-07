# Report diagnostico clima (v1.7)

Periodo: da 2026-11-06 09:13 a 2026-11-06 09:22 (Europe/Rome); righe lette: 750; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

## 0. Segnali automatici

- camera_grande [esito]: sensore in stato di non-valutazione (100% del tempo: in_corso 100%) — la sessione non si completa mai
- camera_grande [esito]: 'ultima_aggiornamento_dati' sempre N/A — timestamp di sessione mai scritto
- cucina [esito_base]: nessuna transizione verso efficace/inefficace nel periodo
- camera_grande [esito_base]: nessuna transizione verso efficace/inefficace nel periodo
- camera [esito_base]: nessuna transizione verso efficace/inefficace nel periodo
- bagno [esito_base]: nessuna transizione verso efficace/inefficace nel periodo
- sala [esito_base]: nessuna transizione verso efficace/inefficace nel periodo
- cucina: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- camera_grande: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- camera: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- corridoio: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- bagno: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- sala: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- 100% delle micro-cadute (16/16) avviene nello stesso minuto su >= 3 entita': causa comune (gateway/integrazione/rete), non dei singoli dispositivi
- fancoil: switch.attiva_fancoil unavailable/unknown per il 2.5% del periodo
- fancoil: switch.attiva_pdc unavailable/unknown per il 2.5% del periodo
- fancoil: switch.attiva_pompa_circolazione unavailable/unknown per il 2.5% del periodo
- fancoil: binary_sensor.pdc_acqua_calda unavailable/unknown per il 2.5% del periodo
- fancoil: sensor.fancoil_cucina_temperature_difference unavailable/unknown per il 1.7% del periodo
- fancoil: sensor.fancoil_camera_grande_temperature_difference unavailable/unknown per il 1.7% del periodo
- fancoil: sensor.fancoil_camera_temperature_difference unavailable/unknown per il 1.7% del periodo
- fancoil: sensor.fancoil_corridoio_temperature_difference unavailable/unknown per il 1.6% del periodo
- fancoil: sensor.fancoil_bagno_temperature_difference unavailable/unknown per il 1.7% del periodo
- fancoil: sensor.fancoil_sala_temperature_difference unavailable/unknown per il 1.7% del periodo
- fancoil: nessun minuto con condizioni abilitanti (tre switch globali on, modo heat/cool, stop off): le velocita' non sono valutabili (PDC spenta?)
- nessuna apertura finestra registrata nel periodo


## 1. Entita' attese (esistenza e righe nel periodo)

- Attese: 152; assenti nel recorder: 3; presenti ma senza righe nel periodo: 0

**Assenti (mai registrate):** sensor.esito_ultimo_consiglio_finestra_corridoio_con_validazione, sensor.esito_ultimo_consiglio_finestra_corridoio_validated, sensor.esito_ultimo_consiglio_finestra_corridoio_validated_v3


**Entita' 'esito' / 'fancoil_events' presenti nel recorder:** automation.bagno_notifica_esito_consiglio_finestra, automation.camera_grande_notifica_esito_consiglio_finestra, automation.camera_notifica_esito_consiglio_finestra, automation.corridoio_notifica_esito_consiglio_finestra, automation.cucina_notifica_esito_consiglio_finestra, automation.reset_sessione_esito_bloccata_bagno, automation.reset_sessione_esito_bloccata_camera, automation.reset_sessione_esito_bloccata_camera_grande, automation.reset_sessione_esito_bloccata_cucina, automation.reset_sessione_esito_bloccata_sala, automation.sala_notifica_esito_consiglio_finestra, sensor.esito_ultimo_consiglio_finestra_bagno_con_validazione, sensor.esito_ultimo_consiglio_finestra_bagno_validated, sensor.esito_ultimo_consiglio_finestra_bagno_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_validated, sensor.esito_ultimo_consiglio_finestra_camera_validated_v3, sensor.esito_ultimo_consiglio_finestra_cucina_con_validazione, sensor.esito_ultimo_consiglio_finestra_cucina_validated, sensor.esito_ultimo_consiglio_finestra_cucina_validated_v3, sensor.esito_ultimo_consiglio_finestra_sala_con_validazione, sensor.esito_ultimo_consiglio_finestra_sala_validated, sensor.esito_ultimo_consiglio_finestra_sala_validated_v3


**Candidati contatto/finestra trovati nel recorder** (quota di tempo):

| entita | righe | on | off | unavailable |
|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 2 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_cucina_not_used | 2 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 2 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_not_used | 2 | 0 | 0.99 | 0.01 |
| binary_sensor.finestracucina_alert | 2 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 3 | 0 | 0.99 | 0.01 |
| binary_sensor.finestracucina_motion | 2 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 3 | 0 | 0.99 | 0.01 |
| binary_sensor.garage_door_contact_filtered | 3 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 1 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 1 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 1 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 1 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 3 | 0 | 0.99 | 0.01 |
| input_boolean.finestra_bagno_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_camera_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_cucina_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_sala_aperta | 0 | 0 | 0 | - |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 5 | 0.05 | 121.85 | 53 | 53 | 53.97 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 4 | 1.44 | 7.78 | 53 | 53 | 53.98 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 4 | 0.10 | 8.67 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| cucina | t_reale | 4 | 0.05 | 8.50 | 17.20 | 17.20 | 17.20 | 0 | 0 | 0 | False | - |
| cucina | t_fancoil | 3 | 1.44 | 7.33 | 17.20 | 17.20 | 17.20 | 0 | 0 | 0 | False | - |
| cucina | omega | 6 | 0.05 | 8.48 | 6.81 | 6.81 | 6.93 | 0 | 0 | 0 | False | 0.13 |
| camera_grande | rh_pilota | 4 | 0.04 | 8.48 | 54 | 54 | 54 | 0 | 0 | 0 | False | - |
| camera_grande | rh_fancoil | 3 | 0.99 | 6.08 | 54 | 54 | 54 | 0 | 0 | 0 | False | - |
| camera_grande | rh_th | 4 | 0.10 | 8.67 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| camera_grande | t_reale | 9 | 0.04 | 5.20 | 17.20 | 17.40 | 17.60 | 0 | 0 | 0 | False | 0.40 |
| camera_grande | t_fancoil | 11 | 0.99 | 4.77 | 17.20 | 17.40 | 17.60 | 0 | 0 | 0 | False | 0.40 |
| camera_grande | omega | 10 | 0.05 | 4.40 | 6.94 | 7.12 | 7.12 | 0 | 0 | 0 | False | 0.18 |
| camera | rh_pilota | 4 | 0.04 | 8.48 | 49 | 49 | 49 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 3 | 1.39 | 7.19 | 49 | 49 | 49 | 0 | 0 | 0 | False | - |
| camera | rh_th | 4 | 0.10 | 8.67 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| camera | t_reale | 4 | 0.04 | 8.48 | 18.40 | 18.40 | 18.40 | 0 | 0 | 0 | False | - |
| camera | t_fancoil | 3 | 1.39 | 7.19 | 18.40 | 18.40 | 18.40 | 0 | 0 | 0 | False | - |
| camera | omega | 5 | 0.05 | 4.37 | 6.79 | 6.79 | 6.79 | 0 | 0 | 0 | False | - |
| corridoio | rh_pilota | 4 | 0.05 | 8.49 | 48 | 48 | 48 | 0 | 0 | 0 | False | - |
| corridoio | rh_fancoil | 3 | 1.37 | 7.12 | 48 | 48 | 48 | 0 | 0 | 0 | False | - |
| corridoio | t_reale | 34 | 0.05 | 4.56 | 18.40 | 18.40 | 18.80 | 0 | 0 | 0 | False | 0.40 |
| corridoio | t_fancoil | 33 | 1.25 | 4.56 | 18.40 | 18.40 | 18.80 | 0 | 0 | 0 | False | 0.40 |
| corridoio | omega | 35 | 0.04 | 4.47 | 6.65 | 6.65 | 6.82 | 0 | 0 | 0 | False | 0.17 |
| bagno | rh_pilota | 6 | 0.04 | 81.56 | 54 | 54 | 55.96 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 5 | 1.31 | 95.65 | 54 | 54.50 | 55.97 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 4 | 0.04 | 8.47 | 17.60 | 17.60 | 17.60 | 0 | 0 | 0 | False | - |
| bagno | t_fancoil | 3 | 1.32 | 7.00 | 17.60 | 17.60 | 17.60 | 0 | 0 | 0 | False | - |
| bagno | omega | 7 | 0.05 | 44.98 | 7.12 | 7.12 | 7.37 | 0 | 0 | 0 | False | 0.13 |
| sala | rh_pilota | 5 | 0.05 | 18.91 | 49 | 49.50 | 50 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 4 | 1.33 | 7.21 | 49 | 49 | 49.98 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 4 | 0.06 | 8.51 | 18.40 | 18.40 | 18.40 | 0 | 0 | 0 | False | - |
| sala | t_fancoil | 3 | 1.34 | 7.05 | 18.40 | 18.40 | 18.40 | 0 | 0 | 0 | False | - |
| sala | omega | 7 | 0.05 | 4.38 | 6.79 | 6.86 | 6.93 | 0 | 0 | 0 | False | 0.14 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 1.26 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 1.22 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 320 | 33.33 | 1 | 263.49 | nessuna_azione 100%, unavailable 0% |
| camera_grande | 320 | 33.33 | 1 | 263.38 | nessuna_azione 100%, unavailable 0% |
| camera | 320 | 33.33 | 1 | 263.38 | nessuna_azione 100%, unavailable 0% |
| corridoio | 320 | 33.33 | 1 | 263.38 | nessuna_azione 100%, unavailable 0% |
| bagno | 320 | 33.33 | 1 | 263.38 | nessuna_azione 100%, unavailable 0% |
| sala | 320 | 33.33 | 1 | 263.37 | nessuna_azione 100%, unavailable 0% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 320 | 0 | 0 | 0 | 0 |
| camera_grande | 320 | 0 | 0 | 0 | 0 |
| camera | 320 | 0 | 0 | 0 | 0 |
| corridoio | 320 | 0 | 0 | 0 | 0 |
| bagno | 320 | 0 | 0 | 0 | 0 |
| sala | 320 | 0 | 0 | 0 | 0 |


**Soglie effettive quando la regola grezza (azione_raw) dice 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):

_nessun dato_

## 4b. Cause dei cambi della regola grezza (azione_raw)

| stanza | transizioni_raw | per_ora | impianto | finestra | trend | soglia_numerica | dati_non_validi | impianto_cambi_per_ora |
|---|---|---|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| camera_grande | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| camera | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| bagno | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| sala | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

_Ogni transizione di azione_raw e' attribuita al primo attributo cambiato rispetto alla riga precedente (priorita': dati, impianto, finestra, trend, poi soglie numeriche)._

## 4c. Derivata dell'umidita': rumore e comportamento della regola 'RH sale -> chiudi'
Pendenza su 3 minuti. Soglie provate: RH > 0.15 %/min, omega > 0.03 g/kg/min, per almeno 2 minuti consecutivi.

**A finestra chiusa (esclusi 20 min dopo ogni chiusura)** - con la finestra chiusa non dovrebbe scattare nulla:

_nessun dato_

_Nessuna apertura >= 5 minuti nel periodo: la parte sulle aperture non e' valutabile._

## 5. Esito ultimo consiglio, sensore '_validated_v3' (Layer 2 attivo)

| stanza | righe | stati | transizioni | efficace | inefficace | in_corso | unavailable_pct | restored |
|---|---|---|---|---|---|---|---|---|
| cucina | 4 | efficace 100%, unavailable 0% | 3 | 2 | 0 | 0 | 25 | False |
| camera_grande | 14 | in_corso 100%, unavailable 0% | 3 | 0 | 0 | 2 | 7.14 | False |
| camera | 4 | efficace 100%, unavailable 0% | 3 | 2 | 0 | 0 | 25 | False |
| corridoio | 0 | (nessuna riga) | 0 | 0 | 0 | 0 | - | False |
| bagno | 4 | inefficace 100%, unavailable 0% | 3 | 0 | 2 | 0 | 25 | False |
| sala | 4 | efficace 100%, unavailable 0% | 3 | 2 | 0 | 0 | 25 | False |

**Stato sensore e attributi di sessione/qualita'** (0 = mai valorizzati):

| stanza | stato | consiglio_valutato | ora_inizio_valutazione | umidita_inizio | tipo_azione | esito_15m | esito_30m | esito_60m | troppo_vecchi_pct | eta_dati_med | eta_dati_sentinella | ultima_aggiornamento_na | note_moda |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | vivo | 3 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | - | False | True | - |
| camera_grande | vivo | 13 | 13 | 13 | 13 | 0 | 0 | 0 | 0 | - | False | True | - |
| camera | vivo | 3 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | - | False | True | - |
| bagno | vivo | 3 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | - | False | True | - |
| sala | vivo | 3 | 3 | 3 | 3 | 0 | 0 | 0 | 0 | - | False | True | - |

## 5b. Esito ultimo consiglio, sensore '_validated' (versione precedente, se ancora attivo)

| stanza | righe | stati | transizioni | efficace | inefficace | in_corso | unavailable_pct | restored |
|---|---|---|---|---|---|---|---|---|
| cucina | 1 | non_valutabile
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p" 100% | 1 | 0 | 0 | 0 | 0 | False |
| camera_grande | 1 | non_valutabile
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p"
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p" 100% | 1 | 0 | 0 | 0 | 0 | False |
| camera | 1 | non_valutabile
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p"
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p" 100% | 1 | 0 | 0 | 0 | 0 | False |
| bagno | 1 | non_valutabile
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p"
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p" 100% | 1 | 0 | 0 | 0 | 0 | False |
| sala | 1 | non_valutabile
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p"
attributes:
  
  oi: "N/A"
  ta: "n"
  cv: "n/a"
  u0: "n/a"
  e15: "n"
  e30: "n"
  e60: "n"
  
  dv: "p" 100% | 1 | 0 | 0 | 0 | 0 | False |

**Stato sensore e attributi di sessione/qualita'** (0 = mai valorizzati):

| stanza | stato | consiglio_valutato | ora_inizio_valutazione | umidita_inizio | tipo_azione | esito_15m | esito_30m | esito_60m | troppo_vecchi_pct | eta_dati_med | eta_dati_sentinella | ultima_aggiornamento_na | note_moda |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | vivo | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | - | False | True | - |
| camera_grande | vivo | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | - | False | True | - |
| camera | vivo | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | - | False | True | - |
| bagno | vivo | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | - | False | True | - |
| sala | vivo | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | - | False | True | - |

## 6. Analytics, log manuale e previsione

| stanza | analytics_righe | attr_distinti | override_rate | accuracy | pred_count | f_rh | attributi_variabili | log_stati | prev_h_p50 | prev_h_8min_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| cucina | 4 | 2 | 0 | 0 | 0 | 1.0 | - | idle 3, unavailable 1 | 5 | 0 |
| camera_grande | 4 | 2 | 0 | 0 | 0 | 1.0 | - | idle 3, unavailable 1 | 5 | 0 |
| camera | 4 | 2 | 0 | 0 | 0 | 1.0 | - | idle 3, unavailable 1 | 5 | 0 |
| corridoio | 4 | 2 | 0 | 0 | 0 | 1.0 | - | idle 3, unavailable 1 | 5 | 0 |
| bagno | 4 | 2 | 0 | 0 | 0 | 1.0 | - | idle 3, unavailable 1 | 5 | 0 |
| sala | 4 | 2 | 0 | 0 | 0 | 1.0 | - | idle 3, unavailable 1 | 5 | 0 |

_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._


## 7. Efficacia delle aperture (osservata)

_Nessuna apertura finestra nel periodo: impossibile valutare efficacia._


## 8. Consigli 'apri' (episodi >= 60 s) seguiti da un'apertura entro 15 min

| stanza | episodi_apri_tot | episodi_ge60s | durata_med_min | seguiti | seguiti_pct | tempo_in_apri_pct |
|---|---|---|---|---|---|---|
| cucina | 0 | 0 | - | 0 | - | 0 |
| camera_grande | 0 | 0 | - | 0 | - | 0 |
| camera | 0 | 0 | - | 0 | - | 0 |
| bagno | 0 | 0 | - | 0 | - | 0 |
| sala | 0 | 0 | - | 0 | - | 0 |

_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._

## 9. Coerenza tra sensori

| stanza | pilota_vs_th_n | pilota_vs_th_p50 | pilota_vs_th_p95 | oltre15_pct | omega_n | omega_bias_med | omega_abs_p95 |
|---|---|---|---|---|---|---|---|
| cucina | 1 | 3 | 3 | 0 | 1 | 0.15 | 0.15 |
| camera_grande | 1 | 4 | 4 | 0 | 1 | 0.16 | 0.16 |
| camera | 1 | 1 | 1 | 0 | 1 | 0.15 | 0.15 |
| corridoio | - | - | - | - | 1 | 0.15 | 0.15 |
| bagno | - | - | - | - | 1 | 0.16 | 0.16 |
| sala | - | - | - | - | 1 | 0.16 | 0.16 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=4.3, p10=4.3, p50=4.3, p90=4.7, max=4.7; RH_ext min=92, p10=92, p50=93, p90=93, max=93; omega_ext min=4.78, p10=4.78, p50=4.78, p90=4.89, max=4.91; fonti: meteo_castionetto 5, (vuota) 1


**Pioggia:** 0.0% dei campioni > 0 (n=1).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| meteo_castionetto | 5 | 0 | 4.70 | 4.91 | 93 |
| (vuota) | 1 | 0 | - | - | - |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 1 | 1 | 0.11 | 0.11 | 11-06 09:13 | 0 | 9h:1 |
| sensor.fancoil_cucina_humidity | 1 | 1 | 0.13 | 0.13 | 11-06 09:13 | 0 | 9h:1 |
| sensor.umidita_cucina_pilota | 1 | 1 | 0.00 | 0.00 | 11-06 09:17 | 0 | 9h:1 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 1 | 1 | 0.11 | 0.11 | 11-06 09:13 | 0 | 9h:1 |
| sensor.fancoil_camera_grande_humidity | 1 | 1 | 0.09 | 0.09 | 11-06 09:13 | 0 | 9h:1 |
| sensor.umidita_camera_grande_pilota | 1 | 1 | 0.00 | 0.00 | 11-06 09:17 | 0 | 9h:1 |
| sensor.fancoil_camera_humidity | 1 | 1 | 0.13 | 0.13 | 11-06 09:13 | 0 | 9h:1 |
| sensor.umidita_camera_pilota | 1 | 1 | 0.00 | 0.00 | 11-06 09:17 | 0 | 9h:1 |
| sensor.fancoil_corridoio_humidity | 1 | 1 | 0.12 | 0.12 | 11-06 09:13 | 0 | 9h:1 |
| sensor.umidita_corridoio_pilota | 1 | 1 | 0.00 | 0.00 | 11-06 09:17 | 0 | 9h:1 |
| sensor.fancoil_bagno_humidity | 1 | 1 | 0.12 | 0.12 | 11-06 09:13 | 0 | 9h:1 |
| sensor.umidita_bagno_pilota | 1 | 1 | 0.00 | 0.00 | 11-06 09:17 | 0 | 9h:1 |
| sensor.fancoil_sala_humidity | 1 | 1 | 0.12 | 0.12 | 11-06 09:13 | 0 | 9h:1 |
| sensor.umidita_sala_pilota | 1 | 1 | 0.00 | 0.00 | 11-06 09:17 | 0 | 9h:1 |
| binary_sensor.contact_cucina_not_used | 1 | 1 | 0.11 | 0.11 | 11-06 09:13 | 0 | 9h:1 |
| binary_sensor.finestra_camera_grande_not_used | 1 | 1 | 0.11 | 0.11 | 11-06 09:13 | 0 | 9h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 0 | 0 | 0 | 0 | 0 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 0 | 0 | 0 | 0 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 9d. Sincronia delle micro-cadute (< 10 min)

- Episodi totali: 16; in minuti con >= 3 entita' contemporaneamente: 16 (100%)

| minuto | n_entita | durata_med_s | esempi |
|---|---|---|---|
| 11-06 09:13 | 16 | 7.16 | contact_cucina_contact, contact_cucina_not_use, fancoil_bagno_humidity |


## 12. Fancoil: disponibilita', coerenza e logica (v1.7)

### 12a. Disponibilita' delle entita' di controllo

| entita | righe | unavail_pct | quote_stati |
|---|---|---|---|
| input_select.fancoil_system_hvac_mode | 1 | 0 | heat 100% |
| switch.attiva_fancoil | 2 | 2.48 | on 98%; unavailable 2% |
| switch.attiva_pdc | 2 | 2.48 | off 98%; unavailable 2% |
| switch.attiva_pompa_circolazione | 2 | 2.48 | on 98%; unavailable 2% |
| binary_sensor.pdc_acqua_calda | 3 | 2.48 | off 98%; unavailable 2% |
| input_select.fancoil_cucina_hvac_mode_local | 1 | 0 | off 100% |
| input_boolean.fancoil_cucina_hvac_mode_follow_master | 1 | 0 | on 100% |
| sensor.fancoil_cucina_temperature_difference | 4 | 1.70 | 5.2 98%; unknown 2%; unavailable 0% |
| binary_sensor.fancoil_cucina_stop_condition | 4 | 0.07 | off 100%; unavailable 0% |
| input_select.fancoil_camera_grande_hvac_mode_local | 1 | 0 | off 100% |
| input_boolean.fancoil_camera_grande_hvac_mode_follow_master | 1 | 0 | on 100% |
| sensor.fancoil_camera_grande_temperature_difference | 9 | 1.70 | 4.8 93%; 5.2 6%; unknown 2%; unavailable 0% |
| binary_sensor.fancoil_camera_grande_stop_condition | 4 | 0.07 | off 100%; unavailable 0% |
| input_select.fancoil_camera_hvac_mode_local | 1 | 0 | off 100% |
| input_boolean.fancoil_camera_hvac_mode_follow_master | 1 | 0 | on 100% |
| sensor.fancoil_camera_temperature_difference | 4 | 1.70 | 4.0 98%; unknown 2%; unavailable 0% |
| binary_sensor.fancoil_camera_stop_condition | 4 | 0.07 | off 100%; unavailable 0% |
| input_select.fancoil_corridoio_hvac_mode_local | 1 | 0 | off 100% |
| input_boolean.fancoil_corridoio_hvac_mode_follow_master | 1 | 0 | on 100% |
| sensor.fancoil_corridoio_temperature_difference | 34 | 1.56 | 4.0 90%; 3.6 9%; unknown 1%; unavailable 0% |
| binary_sensor.fancoil_corridoio_stop_condition | 4 | 0.07 | off 100%; unavailable 0% |
| input_select.fancoil_bagno_hvac_mode_local | 1 | 0 | off 100% |
| input_boolean.fancoil_bagno_hvac_mode_follow_master | 1 | 0 | on 100% |
| sensor.fancoil_bagno_temperature_difference | 4 | 1.70 | 4.8 98%; unknown 2%; unavailable 0% |
| binary_sensor.fancoil_bagno_stop_condition | 4 | 0.07 | off 100%; unavailable 0% |
| input_select.fancoil_sala_hvac_mode_local | 1 | 0 | off 100% |
| input_boolean.fancoil_sala_hvac_mode_follow_master | 1 | 0 | on 100% |
| sensor.fancoil_sala_temperature_difference | 4 | 1.70 | 4.0 98%; unknown 2%; unavailable 0% |
| binary_sensor.fancoil_sala_stop_condition | 4 | 0.08 | off 100%; unavailable 0% |


### 12b. Cambi del modo master

_nessun cambio nel periodo_


### 12c. Coerenza del sensore differenza (atteso: setpoint - corrente; in cool corrente - setpoint)

| stanza | min_con_attributi_climate | diff_assente_min | diff_errata_min | diff_zero_fittizio_min | diff_errata_pct | min_in_cool |
|---|---|---|---|---|---|---|
| cucina | 10 | 0 | 0 | 0 | 0 | 0 |
| camera_grande | 10 | 0 | 0 | 0 | 0 | 0 |
| camera | 10 | 0 | 0 | 0 | 0 | 0 |
| corridoio | 10 | 0 | 0 | 0 | 0 | 0 |
| bagno | 10 | 0 | 0 | 0 | 0 | 0 |
| sala | 10 | 0 | 0 | 0 | 0 | 0 |


_Conta solo anomalie di almeno 5 min consecutivi (diff_errata include i minuti di zero fittizio e di assenza di segno corretto in cool); modo effettivo = master se 'segue master' e' on, altrimenti locale._


### 12d. Violazioni della logica ventola (>= 3 min consecutivi)

| stanza | min_ventola_on | on_con_switch_globali_off | on_con_modo_off | vel_ge2_con_stop_on | min_condizioni_abilitanti |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 0 | 0 |
| camera_grande | 0 | 0 | 0 | 0 | 0 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0 | 0 | 0 | 0 | 0 |
| sala | 0 | 0 | 0 | 0 | 0 |


### 12e. Velocita' osservata per fascia di differenza (solo con condizioni abilitanti)

_nessun dato_


_Condizioni abilitanti: tre switch globali on, modo effettivo heat/cool, stop_condition non on, pdc_acqua_calda non on (ipotesi: con pdc_acqua_calda on il fan_target forza idle). Servono per ricavare le soglie reali e controllare che la velocita' cresca con la differenza._


### 12f. Avvii di Home Assistant e tempi di ripristino

_nessun avvio nel periodo_

## 10. Impronta sul recorder

- Righe totali nel periodo: 7101; entita' del sistema clima (nome contiene stanza e sensore tipo): 1015 (14.3%)

| entita | righe |
|---|---|
| sensor.potenza_carichi_non_misurati | 174 |
| sensor.consumo_casa_rapido | 103 |
| sensor.consumo_impianto_nuovo | 102 |
| sensor.potenza_consumo_casa_reale | 73 |
| automation.ev_listener_eventi_log | 61 |
| sensor.potenza_carica_batteria | 60 |
| sensor.locale_tecnico_solarnet_power_battery_charge | 59 |
| sensor.knx_interface_telegrams | 59 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 56 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 56 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 56 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 55 |
| sensor.consumo_netto_pdc | 55 |
| sensor.smart_meter_2026_a_pdc_total_power | 55 |
| sensor.smart_meter_2026_a_pdc_voltage_a | 54 |
| sensor.locale_tecnico_solarnet_power_grid_export | 54 |
| sensor.smart_meter_2026_a_pdc_power_a | 54 |
| sensor.smart_meter_2026_a_pdc_current_a | 53 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_b | 52 |
| sensor.smart_meter_2026_a_pdc_power_b | 51 |
