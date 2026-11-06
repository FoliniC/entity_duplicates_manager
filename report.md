# Report diagnostico clima (v1.3)

Periodo: da 2026-11-05 14:57 a 2026-11-05 15:57 (Europe/Rome); righe lette: 2447; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

## 0. Segnali automatici

- camera_grande: il consiglio cambia stato ogni 52s (mediana): glitch da trigger multipli, serve debounce
- cucina [esito]: sensore sensor.esito_ultimo_consiglio_finestra_cucina_con_validazione e' quasi sempre unavailable (100% del tempo)
- camera_grande [esito]: sensore sensor.esito_ultimo_consiglio_finestra_camera_grande_con_validazione e' quasi sempre unavailable (100% del tempo)
- camera [esito]: sensore sensor.esito_ultimo_consiglio_finestra_camera_con_validazione e' quasi sempre unavailable (100% del tempo)
- bagno [esito]: sensore sensor.esito_ultimo_consiglio_finestra_bagno_con_validazione e' quasi sempre unavailable (100% del tempo)
- sala [esito]: sensore sensor.esito_ultimo_consiglio_finestra_sala_con_validazione e' quasi sempre unavailable (100% del tempo)
- cucina: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- camera_grande: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- camera: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- corridoio: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- bagno: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- sala: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- nessuna apertura finestra registrata nel periodo


## 1. Entita' attese (esistenza e righe nel periodo)

- Attese: 117; assenti nel recorder: 7; presenti ma senza righe nel periodo: 0

**Assenti (mai registrate):** sensor.esito_ultimo_consiglio_finestra_bagno, sensor.esito_ultimo_consiglio_finestra_camera, sensor.esito_ultimo_consiglio_finestra_camera_grande, sensor.esito_ultimo_consiglio_finestra_corridoio, sensor.esito_ultimo_consiglio_finestra_corridoio_con_validazione, sensor.esito_ultimo_consiglio_finestra_cucina, sensor.esito_ultimo_consiglio_finestra_sala


**Entita' 'esito' / 'fancoil_events' presenti nel recorder:** automation.bagno_notifica_esito_consiglio_finestra, automation.camera_grande_notifica_esito_consiglio_finestra, automation.camera_notifica_esito_consiglio_finestra, automation.corridoio_notifica_esito_consiglio_finestra, automation.cucina_notifica_esito_consiglio_finestra, automation.reset_sessione_esito_bloccata_bagno, automation.reset_sessione_esito_bloccata_camera, automation.reset_sessione_esito_bloccata_camera_grande, automation.reset_sessione_esito_bloccata_cucina, automation.reset_sessione_esito_bloccata_sala, automation.sala_notifica_esito_consiglio_finestra, sensor.esito_ultimo_consiglio_finestra_bagno_con_validazione, sensor.esito_ultimo_consiglio_finestra_bagno_validated, sensor.esito_ultimo_consiglio_finestra_bagno_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_validated, sensor.esito_ultimo_consiglio_finestra_camera_validated_v3, sensor.esito_ultimo_consiglio_finestra_cucina_con_validazione, sensor.esito_ultimo_consiglio_finestra_cucina_validated, sensor.esito_ultimo_consiglio_finestra_cucina_validated_v3, sensor.esito_ultimo_consiglio_finestra_sala_con_validazione, sensor.esito_ultimo_consiglio_finestra_sala_validated, sensor.esito_ultimo_consiglio_finestra_sala_validated_v3


**Candidati contatto/finestra trovati nel recorder** (quota di tempo):

| entita | righe | on | off | unavailable |
|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 16 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_cucina_not_used | 16 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 16 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_not_used | 16 | 0 | 0.99 | 0.01 |
| binary_sensor.finestracucina_alert | 16 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 24 | 0 | 1.00 | 0.00 |
| binary_sensor.finestracucina_motion | 16 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 24 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 16 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 8 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 8 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 8 | 0 | 1.00 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 8 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 26 | 0.01 | 0.98 | 0.02 |
| input_boolean.finestra_bagno_aperta | 8 | 0 | 1 | 0 |
| input_boolean.finestra_camera_aperta | 8 | 0 | 1 | 0 |
| input_boolean.finestra_camera_grande_aperta | 8 | 1 | 0 | 0 |
| input_boolean.finestra_corridoio_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_cucina_aperta | 8 | 1 | 0 | 0 |
| input_boolean.finestra_sala_aperta | 8 | 0 | 1.00 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 17 | 0.04 | 266.12 | 53 | 53 | 53 | 0 | 0 | 0 | False | - |
| cucina | rh_fancoil | 17 | 1.53 | 42.25 | 53 | 53 | 53 | 0 | 0 | 0 | False | - |
| cucina | rh_th | 17 | 0.09 | 266.13 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| cucina | t_reale | 23 | 0.04 | 169.32 | 18.40 | 18.80 | 19.20 | 0 | 0 | 0 | False | 0.40 |
| cucina | t_fancoil | 22 | 1.53 | 9.49 | 18.40 | 18.80 | 19.20 | 0 | 0 | 0 | False | 0.40 |
| cucina | omega | 30 | 0.03 | 21.96 | 7.32 | 7.51 | 7.71 | 0 | 0 | 0 | False | 0.19 |
| camera_grande | rh_pilota | 19 | 0.03 | 249.81 | 53 | 53 | 54 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 19 | 1.70 | 43.64 | 53 | 53 | 54 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 17 | 0.10 | 266.13 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| camera_grande | t_reale | 59 | 0.03 | 9.41 | 18 | 18.40 | 19.20 | 0 | 0 | 0 | False | 0.40 |
| camera_grande | t_fancoil | 60 | 1.70 | 8.28 | 18 | 18.40 | 19.20 | 0 | 0 | 0 | False | 0.40 |
| camera_grande | omega | 65 | 0.04 | 9.13 | 7.14 | 7.46 | 7.71 | 0 | 0 | 0 | False | 0.18 |
| camera | rh_pilota | 17 | 0.03 | 266.11 | 48 | 48 | 48 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 17 | 1.55 | 42.24 | 48 | 48 | 48 | 0 | 0 | 0 | False | - |
| camera | rh_th | 17 | 0.10 | 266.13 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| camera | t_reale | 17 | 0.03 | 266.11 | 18.80 | 18.80 | 18.80 | 0 | 0 | 0 | False | - |
| camera | t_fancoil | 17 | 1.55 | 42.24 | 18.80 | 18.80 | 18.80 | 0 | 0 | 0 | False | - |
| camera | omega | 22 | 0.04 | 226.75 | 6.79 | 6.79 | 6.80 | 0 | 0 | 0 | False | 0.01 |
| corridoio | rh_pilota | 23 | 0.04 | 157.43 | 49 | 49 | 50 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 23 | 1.70 | 88.57 | 49 | 49 | 50 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 22 | 0.04 | 127.89 | 19.60 | 19.60 | 20 | 0 | 0 | 0 | False | 0.40 |
| corridoio | t_fancoil | 22 | 1.70 | 10.33 | 19.60 | 19.60 | 20 | 0 | 0 | 0 | False | 0.40 |
| corridoio | omega | 40 | 0.04 | 4.04 | 7.30 | 7.45 | 7.64 | 0 | 0 | 0 | False | 0.16 |
| bagno | rh_pilota | 20 | 0.03 | 255.82 | 53 | 53 | 54 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 20 | 1.72 | 74.99 | 53 | 53.50 | 54 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 52 | 0.03 | 10.52 | 18.40 | 18.60 | 19.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 51 | 1.72 | 7.87 | 18.40 | 18.60 | 19.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 59 | 0.04 | 9.93 | 7.32 | 7.42 | 8 | 0 | 0 | 0 | False | 0.10 |
| sala | rh_pilota | 17 | 0.04 | 266.12 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| sala | rh_fancoil | 17 | 1.56 | 42.22 | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| sala | t_reale | 17 | 0.05 | 266.13 | 19.20 | 19.20 | 19.20 | 0 | 0 | 0 | False | - |
| sala | t_fancoil | 17 | 1.56 | 42.22 | 19.20 | 19.20 | 19.20 | 0 | 0 | 0 | False | - |
| sala | omega | 21 | 0.04 | 241.29 | 7.26 | 7.26 | 7.26 | 0 | 0 | 0 | False | - |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 1.45 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 1.40 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0.90 | 50 | 4 | 124.03 | apri 100%, unavailable 0%, nessuna_azione 0% |
| camera_grande | 1 | 54.55 | 4 | 52.11 | apri 92%, nessuna_azione 8%, unavailable 0% |
| camera | 0.80 | 44.44 | 4 | 247.01 | nessuna_azione 100%, unavailable 0% |
| corridoio | 0.80 | 44.44 | 4 | 247.01 | nessuna_azione 100%, unavailable 0% |
| bagno | 0.90 | 40 | 4 | 239.64 | nessuna_azione 87%, apri 13%, unavailable 0% |
| sala | 0.80 | 44.44 | 4 | 247.00 | nessuna_azione 100%, unavailable 0% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0.90 | 0 | 0 | 0 | 0 |
| camera_grande | 1 | 0.10 | 0.10 | 0.10 | 0 |
| camera | 0.80 | 0 | 0 | 0 | 0 |
| corridoio | 0.80 | 0 | 0 | 0 | 0 |
| bagno | 0.90 | 0.10 | 0.10 | 0.10 | 0 |
| sala | 0.80 | 0 | 0 | 0 | 0 |


**Soglie effettive quando consiglia 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):

| stanza | impianto | ore_apri | dw_min_grezzo | dw_min_stabile30s | dw_p10_t | dw_p50_t | calo_min_stab | calo_p50_t |
|---|---|---|---|---|---|---|---|---|
| cucina | False | 0.41 | 2.34 | 2.34 | 2.34 | 2.47 | 14.30 | 15.50 |
| cucina | True | 0.59 | 2.34 | 2.34 | 2.34 | 2.49 | 13.50 | 14.30 |
| camera_grande | False | 0.47 | 2.34 | 2.34 | 2.34 | 2.47 | 5.20 | 7.70 |
| camera_grande | True | 0.45 | 2.29 | 2.29 | 2.29 | 2.43 | 4.90 | 5.60 |
| bagno | True | 0.13 | 2.44 | 2.44 | 2.44 | 2.58 | 14.10 | 14.40 |

## 5. Esito ultimo consiglio, sensore '_con_validazione' (Layer 2)

| stanza | righe | stati | transizioni | efficace | inefficace | in_corso | unavailable_pct | restored |
|---|---|---|---|---|---|---|---|---|
| cucina | 1 | unavailable 100% | 1 | 0 | 0 | 0 | 100 | False |
| camera_grande | 1 | unavailable 100% | 1 | 0 | 0 | 0 | 100 | False |
| camera | 1 | unavailable 100% | 1 | 0 | 0 | 0 | 100 | False |
| corridoio | 0 | (nessuna riga) | 0 | 0 | 0 | 0 | - | False |
| bagno | 1 | unavailable 100% | 1 | 0 | 0 | 0 | 100 | False |
| sala | 1 | unavailable 100% | 1 | 0 | 0 | 0 | 100 | False |

**Stato sensore e attributi di sessione/qualita'** (0 = mai valorizzati):

| stanza | stato | consiglio_valutato | ora_inizio_valutazione | umidita_inizio | tipo_azione | esito_15m | esito_30m | esito_60m | troppo_vecchi_pct | eta_dati_med | eta_dati_sentinella | ultima_aggiornamento_na | note_moda |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | quasi sempre unavailable | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | False | False | - |
| camera_grande | quasi sempre unavailable | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | False | False | - |
| camera | quasi sempre unavailable | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | False | False | - |
| bagno | quasi sempre unavailable | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | False | False | - |
| sala | quasi sempre unavailable | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | False | False | - |

## 5b. Esito sensore base (Layer 1)

_Nessuna stanza ha un sensore `esito_ultimo_consiglio_finestra_<stanza>` attivo (tutti unavailable/restored): il Layer 1 risulta dismesso. Sezione saltata; le entita' orfane sono segnalate nella sezione 0._

## 6. Analytics, log manuale e previsione

| stanza | analytics_righe | attr_distinti | override_rate | accuracy | pred_count | f_rh | attributi_variabili | log_stati | prev_h_p50 | prev_h_8min_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| cucina | 17 | 2 | 0 | 0 | 0 | 1.0 | - | idle 13, unavailable 4 | 5 | 34.62 |
| camera_grande | 17 | 2 | 0 | 0 | 0 | 1.0 | - | idle 13, unavailable 4 | 5 | 33.33 |
| camera | 17 | 2 | 0 | 0 | 0 | 1.0 | - | idle 13, unavailable 4 | 5 | 0 |
| corridoio | 17 | 2 | 0 | 0 | 0 | 1.0 | - | idle 13, unavailable 4 | 5 | 0 |
| bagno | 17 | 2 | 0 | 0 | 0 | 1.0 | - | idle 13, unavailable 4 | 5 | 0 |
| sala | 17 | 2 | 0 | 0 | 0 | 1.0 | - | idle 13, unavailable 4 | 5 | 0 |

_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._


## 7. Efficacia delle aperture (osservata)

_Nessuna apertura finestra nel periodo: impossibile valutare efficacia._


## 8. Consigli 'apri' (episodi >= 60 s) seguiti da un'apertura entro 15 min

| stanza | episodi_apri_tot | episodi_ge60s | durata_med_min | seguiti | seguiti_pct | tempo_in_apri_pct |
|---|---|---|---|---|---|---|
| cucina | 5 | 5 | 11.17 | 0 | 0 | 99.90 |
| camera_grande | 4 | 4 | 11.12 | 0 | 0 | 91.60 |
| camera | 0 | 0 | - | 0 | - | 0 |
| bagno | 2 | 2 | 3.99 | 0 | 0 | 13.31 |
| sala | 0 | 0 | - | 0 | - | 0 |

_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._

## 9. Coerenza tra sensori

| stanza | pilota_vs_th_n | pilota_vs_th_p50 | pilota_vs_th_p95 | oltre15_pct | omega_n | omega_bias_med | omega_abs_p95 |
|---|---|---|---|---|---|---|---|
| cucina | 12 | 3 | 3 | 0 | 12 | 0.14 | 0.15 |
| camera_grande | 12 | 3 | 4 | 0 | 12 | 0.14 | 0.15 |
| camera | 12 | 2 | 2 | 0 | 12 | 0.12 | 0.13 |
| corridoio | - | - | - | - | 12 | 0.14 | 0.14 |
| bagno | - | - | - | - | 12 | 0.14 | 0.15 |
| sala | - | - | - | - | 12 | 0.14 | 0.14 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=11.3, p10=11.3, p50=11.5, p90=11.7, max=11.7; RH_ext min=57, p10=57, p50=60, p90=63, max=63; omega_ext min=4.85, p10=4.85, p50=5.03, p90=5.22, max=5.22; fonti: meteo_castionetto 19, (vuota) 4


**Pioggia:** 0.0% dei campioni > 0 (n=9).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| meteo_castionetto | 19 | 0 | 11.70 | 5.22 | 63 |
| (vuota) | 4 | 0 | - | - | - |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 8 | 8 | 0.11 | 0.15 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.fancoil_cucina_humidity | 8 | 8 | 0.11 | 0.16 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.umidita_cucina_pilota | 4 | 4 | 0.01 | 0.01 | 11-05 15:31 | 0 | 15h:4 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 8 | 8 | 0.10 | 0.15 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.fancoil_camera_grande_humidity | 8 | 8 | 0.13 | 0.17 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.umidita_camera_grande_pilota | 4 | 4 | 0.01 | 0.01 | 11-05 15:40 | 0 | 15h:4 |
| sensor.fancoil_camera_humidity | 8 | 8 | 0.12 | 0.16 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.umidita_camera_pilota | 4 | 4 | 0.01 | 0.01 | 11-05 15:40 | 0 | 15h:4 |
| sensor.fancoil_corridoio_humidity | 8 | 8 | 0.13 | 0.17 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.umidita_corridoio_pilota | 4 | 4 | 0.01 | 0.01 | 11-05 15:31 | 0 | 15h:4 |
| sensor.fancoil_bagno_humidity | 8 | 8 | 0.13 | 0.17 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.umidita_bagno_pilota | 4 | 4 | 0.00 | 0.01 | 11-05 15:31 | 0 | 15h:4 |
| sensor.fancoil_sala_humidity | 8 | 8 | 0.12 | 0.16 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| sensor.umidita_sala_pilota | 4 | 4 | 0.01 | 0.01 | 11-05 15:31 | 0 | 15h:4 |
| binary_sensor.contact_cucina_not_used | 8 | 8 | 0.11 | 0.15 | 11-05 15:48 | 0 | 15h:7, 14h:1 |
| binary_sensor.finestra_camera_grande_not_used | 8 | 8 | 0.10 | 0.15 | 11-05 15:48 | 0 | 15h:7, 14h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 0 | 0 | 0 | 0 | 0 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 0 | 0 | 0 | 0 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 56303; entita' del sistema clima (nome contiene stanza e sensore tipo): 5214 (9.3%)

| entita | righe |
|---|---|
| sensor.potenza_carichi_non_misurati | 1720 |
| sensor.consumo_casa_rapido | 1313 |
| sensor.net_grid_power | 984 |
| sensor.prism_potenza | 727 |
| sensor.locale_tecnico_prism_power_provided_to_car | 719 |
| sensor.prism_potenza_kw | 684 |
| sensor.ev_charge_2025_power_from_solar | 684 |
| sensor.consumo_impianto_nuovo | 647 |
| sensor.prism_tensione_attuale | 584 |
| sensor.locale_tecnico_prism_power_grid_voltage | 576 |
| sensor.potenza_totale_bilancio | 431 |
| sensor.potenza_consumo_casa_reale | 424 |
| sensor.potenza_totale_entrante | 417 |
| sensor.ev_charging_status_markdown | 392 |
| automation.log_ev_charging_reason_changes | 356 |
| sensor.knx_interface_telegrams | 349 |
| sensor.locale_tecnico_solarnet_power_battery_discharge | 339 |
| sensor.potenza_scarica_batteria | 339 |
| sensor.locale_tecnico_solarnet_power_load_consumed | 339 |
| sensor.ev_charging_estimated_current | 337 |
