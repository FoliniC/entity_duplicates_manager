# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 07:21 a 2026-10-29 10:21 (Europe/Rome); righe lette: 13876; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

## 0. Segnali automatici

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
| binary_sensor.contact_cucina_contact_cucina | 12 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_cucina_not_used | 12 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 12 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_not_used | 12 | 0 | 0.99 | 0.01 |
| binary_sensor.finestracucina_alert | 12 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 18 | 1.00 | 0 | 0.00 |
| binary_sensor.finestracucina_motion | 12 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 18 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 6 | 0 | 1.00 | 0 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 6 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 6 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 6 | 0 | 1.00 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 6 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 18 | 0 | 0.99 | 0.01 |
| input_boolean.finestra_bagno_aperta | 6 | 0 | 1 | 0 |
| input_boolean.finestra_camera_aperta | 6 | 0 | 1 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 6 | 0 | 1.00 | 0 |
| input_boolean.finestra_cucina_aperta | 6 | 0 | 1 | 0 |
| input_boolean.finestra_sala_aperta | 6 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 13 | 0 | 664.39 | 45.48 | 54 | 55.76 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 18 | 0.50 | 467.50 | 45.44 | 53.50 | 54 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 9 | 0 | 586.12 | 50.08 | 51 | 53.76 | 0 | 0 | 0 | False | 3 |
| cucina | t_reale | 132 | 0 | 6.85 | 19.20 | 19.60 | 19.60 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 137 | 0.50 | 6.86 | 19.20 | 19.60 | 19.60 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 269 | 0 | 1.75 | 7.14 | 7.92 | 8.07 | 0 | 0 | 0 | False | 0.10 |
| camera_grande | rh_pilota | 12 | 0 | 574.24 | 48.22 | 55.50 | 56 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 17 | 0.47 | 427.29 | 48.40 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 10 | 0 | 437.80 | 50 | 50 | 53.73 | 0 | 0 | 0 | False | 1 |
| camera_grande | t_reale | 190 | 0 | 4.89 | 18 | 19.20 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 195 | 0.47 | 5.00 | 18 | 19.20 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 195 | 0 | 4.98 | 7.03 | 8.02 | 8.16 | 0 | 0 | 0 | False | 0.10 |
| camera | rh_pilota | 7 | 0 | 522.03 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 13 | 0.43 | 165.08 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_th | 7 | 0 | 522.09 | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 46 | 0 | 9.69 | 20 | 20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 52 | 0.43 | 9.02 | 20 | 20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 48 | 0 | 9.69 | 8.43 | 8.43 | 8.55 | 0 | 0 | 0 | False | 0.11 |
| corridoio | rh_pilota | 16 | 0.06 | 320.51 | 42.42 | 51 | 51 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 21 | 0.55 | 221.93 | 42.39 | 50.50 | 51 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 91 | 0 | 7.45 | 20.36 | 20.60 | 20.84 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 98 | 0.55 | 6.38 | 20.40 | 20.60 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 192 | 0.06 | 1.78 | 7.06 | 8.11 | 8.23 | 0 | 0 | 0 | False | 0.10 |
| bagno | rh_pilota | 13 | 0 | 513.99 | 47.12 | 55 | 56.76 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 18 | 0.48 | 317.78 | 47.11 | 54.50 | 55 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 37 | 0 | 10.46 | 17.56 | 19.40 | 19.93 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 44 | 0.48 | 9.29 | 17.57 | 19.40 | 19.73 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 44 | 0 | 16.79 | 6.09 | 7.68 | 8.52 | 0 | 0 | 0 | False | 0.09 |
| sala | rh_pilota | 11 | 0 | 586.29 | 54 | 54 | 56 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 16 | 0.51 | 427.08 | 54 | 54 | 55.91 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 57 | 0 | 8.05 | 20.20 | 20.40 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 63 | 0.51 | 8.05 | 20.20 | 20.40 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 115 | 0 | 2.82 | 8.54 | 8.65 | 9.14 | 0 | 0 | 0 | False | 0.11 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 0.68 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 0.57 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0.20 | 0 | 0 | 470.13 | nessuna_azione 95%, chiudi 4%, apri 1% |
| camera_grande | 0.20 | 0 | 0 | 470.13 | nessuna_azione 95%, chiudi 4%, apri 1% |
| camera | 0 | 0 | 0 | 10800.49 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 10800.26 | nessuna_azione 100% |
| bagno | 0.20 | 0 | 0 | 470.13 | nessuna_azione 95%, chiudi 4%, apri 1% |
| sala | 0 | 0 | 0 | 10800.17 | nessuna_azione 100% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0.20 | 0.20 | 0.20 | 0.10 | 0.10 |
| camera_grande | 0.20 | 0.20 | 0.20 | 0.10 | 0.10 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0.20 | 0.20 | 0.20 | 0.10 | 0.10 |
| sala | 0 | 0 | 0 | 0 | 0 |


**Soglie effettive quando consiglia 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):

| stanza | impianto | ore_apri | dw_min_grezzo | dw_min_stabile30s | dw_p10_t | dw_p50_t | calo_min_stab | calo_p50_t |
|---|---|---|---|---|---|---|---|---|
| cucina | False | 0.02 | 0.45 | 0.45 | 0.45 | 0.45 | 0.80 | 0.80 |
| camera_grande | False | 0.02 | -0.76 | -0.76 | -0.76 | -0.76 | -1.30 | -1.30 |
| bagno | False | 0.02 | 0.92 | 0.92 | 0.92 | 0.92 | 1.60 | 1.60 |

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
| cucina | 7 | 1 | 0 | 0 | 0 | 1.0 | - | idle 7 | 8 | 99.27 |
| camera_grande | 7 | 1 | 0 | 0 | 0 | 1.0 | - | idle 7 | 8 | 99.36 |
| camera | 7 | 1 | 0 | 0 | 0 | 1.0 | - | idle 7 | 8 | 99.06 |
| corridoio | 7 | 1 | 0 | 0 | 0 | 1.0 | - | idle 7 | 8 | 98.84 |
| bagno | 7 | 2 | 0 | 0 | 0 | 1.0 | override_rate(2): "0",0; consiglio_accuracy(2): "0",100; prediction_factor_humidity(2): "1.0",1.0; prediction_factor_temperature(2): "1.0",1.0; prediction_facto | idle 6, close_concordante 1 | 8 | 99.06 |
| sala | 7 | 1 | 0 | 0 | 0 | 1.0 | - | idle 7 | 8 | 99.09 |

_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._


## 7. Efficacia delle aperture (osservata)

_Nessuna apertura finestra nel periodo: impossibile valutare efficacia._


## 8. Consigli 'apri' (episodi >= 60 s) seguiti da un'apertura entro 15 min

| stanza | episodi_apri_tot | episodi_ge60s | durata_med_min | seguiti | seguiti_pct | tempo_in_apri_pct |
|---|---|---|---|---|---|---|
| cucina | 1 | 1 | 1.17 | 0 | 0 | 0.65 |
| camera_grande | 1 | 1 | 1.17 | 0 | 0 | 0.65 |
| camera | 0 | 0 | - | 0 | - | 0 |
| bagno | 1 | 1 | 1.17 | 0 | 0 | 0.65 |
| sala | 0 | 0 | - | 0 | - | 0 |

_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._

## 9. Coerenza tra sensori

| stanza | pilota_vs_th_n | pilota_vs_th_p50 | pilota_vs_th_p95 | oltre15_pct | omega_n | omega_bias_med | omega_abs_p95 |
|---|---|---|---|---|---|---|---|
| cucina | 36 | 3 | 5 | 0 | 36 | 0.17 | 0.17 |
| camera_grande | 36 | 4 | 6 | 0 | 36 | 0.17 | 0.18 |
| camera | 36 | 9 | 9 | 0 | 36 | 0.19 | 0.19 |
| corridoio | - | - | - | - | 36 | 0.17 | 0.18 |
| bagno | - | - | - | - | 36 | 0.17 | 0.18 |
| sala | - | - | - | - | 36 | 0.19 | 0.19 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=9.6, p10=9.8, p50=15.6, p90=19.1, max=20.0; RH_ext min=41, p10=44, p50=53, p90=67, max=99; omega_ext min=5.13, p10=5.26, p50=6.10, p90=6.52, max=8.19; fonti: clima_locale 632


**Pioggia:** 0.0% dei campioni > 0 (n=7).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 632 | 0 | 20 | 8.19 | 99 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 6 | 6 | 0.19 | 0.43 | 10-29 10:02 | 0 | 10h:3, 9h:2, 7h:1 |
| sensor.fancoil_cucina_humidity | 6 | 6 | 0.15 | 0.21 | 10-29 09:52 | 0 | 10h:3, 9h:2, 7h:1 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 6 | 6 | 0.16 | 0.36 | 10-29 10:02 | 0 | 10h:3, 9h:2, 7h:1 |
| sensor.fancoil_camera_grande_humidity | 6 | 6 | 0.14 | 0.20 | 10-29 10:02 | 0 | 10h:3, 9h:2, 7h:1 |
| sensor.fancoil_camera_humidity | 6 | 6 | 0.13 | 0.19 | 10-29 09:52 | 0 | 10h:3, 9h:2, 7h:1 |
| sensor.fancoil_corridoio_humidity | 7 | 7 | 0.14 | 0.20 | 10-29 09:52 | 0 | 9h:3, 10h:3, 7h:1 |
| sensor.umidita_corridoio_pilota | 1 | 1 | 0.12 | 0.12 | 10-29 09:48 | 0 | 9h:1 |
| sensor.fancoil_bagno_humidity | 6 | 6 | 0.14 | 0.19 | 10-29 10:02 | 0 | 10h:3, 9h:2, 7h:1 |
| sensor.fancoil_sala_humidity | 6 | 6 | 0.15 | 0.20 | 10-29 09:52 | 0 | 10h:3, 9h:2, 7h:1 |
| binary_sensor.contact_cucina_not_used | 6 | 6 | 0.19 | 0.43 | 10-29 10:02 | 0 | 10h:3, 9h:2, 7h:1 |
| binary_sensor.finestra_camera_grande_not_used | 6 | 6 | 0.16 | 0.36 | 10-29 10:02 | 0 | 10h:3, 9h:2, 7h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 0 | 0 | 0 | 0 | 0 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 0 | 0 | 0 | 0 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 98594; entita' del sistema clima (nome contiene stanza e sensore tipo): 24928 (25.3%)

| entita | righe |
|---|---|
| automation.fancoil_listener_eventi_log | 2658 |
| sensor.statistics_temperatura_camera_variance | 1931 |
| sensor.statistics_temperatura_sala_variance | 1927 |
| sensor.statistics_temperatura_camera_grande_variance | 1926 |
| sensor.statistics_temperatura_bagno_variance | 1924 |
| sensor.previsione_finestra_camera_grande | 1870 |
| sensor.consumo_impianto_nuovo | 1743 |
| sensor.previsione_finestra_cucina | 1634 |
| sensor.previsione_finestra_corridoio | 1468 |
| sensor.previsione_finestra_sala | 1324 |
| sensor.previsione_finestra_bagno | 1282 |
| sensor.previsione_finestra_camera | 1278 |
| automation.ev_listener_eventi_log | 1056 |
| sensor.knx_interface_telegrams | 1028 |
| sensor.cucina_calibrazione_riepilogo | 977 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 952 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 951 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 938 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 935 |
| sensor.smart_meter_2026_a_pdc_total_power | 909 |
