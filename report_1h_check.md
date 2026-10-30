# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 13:48 a 2026-10-29 14:48 (Europe/Rome); righe lette: 6658; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

## 0. Segnali automatici

- cucina [esito]: sensore sensor.esito_ultimo_consiglio_finestra_cucina_con_validazione e' quasi sempre unavailable (100% del tempo)
- camera_grande [esito]: sensore sensor.esito_ultimo_consiglio_finestra_camera_grande_con_validazione e' quasi sempre unavailable (100% del tempo)
- camera [esito]: sensore sensor.esito_ultimo_consiglio_finestra_camera_con_validazione e' quasi sempre unavailable (100% del tempo)
- bagno [esito]: sensore sensor.esito_ultimo_consiglio_finestra_bagno_con_validazione e' quasi sempre unavailable (100% del tempo)
- sala [esito]: sensore sensor.esito_ultimo_consiglio_finestra_sala_con_validazione e' quasi sempre unavailable (100% del tempo)
- cucina: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- camera_grande: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)
- corridoio: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)


## 1. Entita' attese (esistenza e righe nel periodo)

- Attese: 117; assenti nel recorder: 7; presenti ma senza righe nel periodo: 0

**Assenti (mai registrate):** sensor.esito_ultimo_consiglio_finestra_bagno, sensor.esito_ultimo_consiglio_finestra_camera, sensor.esito_ultimo_consiglio_finestra_camera_grande, sensor.esito_ultimo_consiglio_finestra_corridoio, sensor.esito_ultimo_consiglio_finestra_corridoio_con_validazione, sensor.esito_ultimo_consiglio_finestra_cucina, sensor.esito_ultimo_consiglio_finestra_sala


**Entita' 'esito' / 'fancoil_events' presenti nel recorder:** automation.bagno_notifica_esito_consiglio_finestra, automation.camera_grande_notifica_esito_consiglio_finestra, automation.camera_notifica_esito_consiglio_finestra, automation.corridoio_notifica_esito_consiglio_finestra, automation.cucina_notifica_esito_consiglio_finestra, automation.reset_sessione_esito_bloccata_bagno, automation.reset_sessione_esito_bloccata_camera, automation.reset_sessione_esito_bloccata_camera_grande, automation.reset_sessione_esito_bloccata_cucina, automation.reset_sessione_esito_bloccata_sala, automation.sala_notifica_esito_consiglio_finestra, sensor.esito_ultimo_consiglio_finestra_bagno_con_validazione, sensor.esito_ultimo_consiglio_finestra_bagno_validated, sensor.esito_ultimo_consiglio_finestra_bagno_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_validated, sensor.esito_ultimo_consiglio_finestra_camera_validated_v3, sensor.esito_ultimo_consiglio_finestra_cucina_con_validazione, sensor.esito_ultimo_consiglio_finestra_cucina_validated, sensor.esito_ultimo_consiglio_finestra_cucina_validated_v3, sensor.esito_ultimo_consiglio_finestra_sala_con_validazione, sensor.esito_ultimo_consiglio_finestra_sala_validated, sensor.esito_ultimo_consiglio_finestra_sala_validated_v3


**Candidati contatto/finestra trovati nel recorder** (quota di tempo):

| entita | righe | on | off | unavailable |
|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 4 | 0.52 | 0.48 | 0 |
| binary_sensor.contact_cucina_not_used | 4 | 0.52 | 0.48 | 0 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 2 | 0.45 | 0.55 | 0 |
| binary_sensor.finestra_camera_grande_not_used | 2 | 0.45 | 0.55 | 0 |
| binary_sensor.finestracucina_alert | 0 | 0 | 0 | - |
| binary_sensor.finestracucina_connected | 0 | 0 | 0 | - |
| binary_sensor.finestracucina_motion | 0 | 0 | 0 | - |
| binary_sensor.finestracucina_recording | 0 | 0 | 0 | - |
| binary_sensor.garage_door_contact_filtered | 0 | 0 | 0 | - |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 0 | 0 | 0 | - |
| binary_sensor.wifi_garage_door_module_garage_contact | 2 | 0.01 | 0.99 | 0 |
| input_boolean.finestra_bagno_aperta | 2 | 0.47 | 0.53 | 0 |
| input_boolean.finestra_camera_aperta | 2 | 0.46 | 0.54 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_cucina_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_sala_aperta | 2 | 0.47 | 0.53 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 11 | 0 | 61.09 | 43.10 | 47 | 53.80 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 11 | 0 | 61.09 | 43.10 | 47 | 53.80 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 1 | 0 | - | 48 | 48 | 48 | 0 | 0 | 0 | False | - |
| cucina | t_reale | 59 | 0 | 6.07 | 21.60 | 22 | 22.20 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 59 | 0 | 6.07 | 21.60 | 22 | 22.20 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 137 | 0 | 0.90 | 7.36 | 7.80 | 9.50 | 0 | 0 | 0 | False | 0.09 |
| camera_grande | rh_pilota | 16 | 0 | 63.54 | 40.15 | 44 | 54.85 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 16 | 0 | 63.54 | 40.15 | 44 | 54.85 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 2 | 0 | 673.22 | 51.01 | 51.50 | 51.99 | 0 | 0 | 0 | False | 1 |
| camera_grande | t_reale | 27 | 0 | 81.13 | 20.45 | 21.40 | 22 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 27 | 0 | 81.13 | 20.45 | 21.40 | 22 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 42 | 0 | 42.37 | 6.38 | 7.39 | 9.39 | 0 | 0 | 0 | False | 0.12 |
| camera | rh_pilota | 13 | 0 | 117.36 | 44.12 | 47 | 53.88 | 0 | 0 | 0 | False | 1 |
| camera | rh_fancoil | 13 | 0 | 117.36 | 44.12 | 47 | 53.88 | 0 | 0 | 0 | False | 1 |
| camera | rh_th | 1 | 0 | - | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 23 | 0 | 77.56 | 20.24 | 21.40 | 22 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 23 | 0 | 77.56 | 20.24 | 21.40 | 22 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 36 | 0 | 43.92 | 6.85 | 7.86 | 9.25 | 0 | 0 | 0 | False | 0.11 |
| corridoio | rh_pilota | 22 | 0 | 120.52 | 38 | 42 | 53 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 22 | 0 | 120.52 | 38 | 42 | 53 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 26 | 0 | 12.13 | 21.40 | 21.80 | 22 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 26 | 0 | 12.13 | 21.40 | 21.80 | 22 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 95 | 0 | 3.11 | 6.34 | 7.35 | 9.21 | 0 | 0 | 0 | False | 0.11 |
| bagno | rh_pilota | 22 | 0 | 60.46 | 39 | 46 | 52.79 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 22 | 0 | 60.46 | 39 | 46 | 52.79 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 65 | 0 | 5.38 | 22 | 22.60 | 23.20 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 65 | 0 | 5.38 | 22 | 22.60 | 23.20 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 86 | 0 | 5.64 | 6.75 | 8.38 | 9.51 | 0 | 0 | 0 | False | 0.11 |
| sala | rh_pilota | 19 | 0.06 | 120.16 | 39.17 | 42 | 54.83 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 19 | 0.06 | 120.16 | 39.17 | 42 | 54.83 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 25 | 0 | 90.64 | 21.05 | 22.20 | 24.42 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 25 | 0.06 | 90.64 | 21.05 | 22.10 | 22.60 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 83 | 0.06 | 0.33 | 6.35 | 7.37 | 11.28 | 0 | 0 | 0 | False | 0.12 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 2 | 7.55 | 12.05 | 25.17 | 0 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 1 | 13.02 | 13.02 | 21.70 | 0 |
| camera | input_boolean.finestra_camera_aperta | 1 | 13.11 | 13.11 | 21.85 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 1 | 13.22 | 13.22 | 22.04 | 0 |
| sala | input_boolean.finestra_sala_aperta | 1 | 13.22 | 13.22 | 22.04 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0.40 | 0 | 0 | 420.00 | nessuna_azione 73%, chiudi 27% |
| camera_grande | 0.50 | 0 | 0 | 300.00 | nessuna_azione 65%, chiudi 22%, mantieni_chiusa 13% |
| camera | 0.20 | 0 | 0 | 900.00 | nessuna_azione 78%, chiudi 22% |
| corridoio | 0.60 | 14.29 | 1 | 119.99 | nessuna_azione 73%, chiudi_porte 27% |
| bagno | 0.30 | 0 | 0 | 779.98 | nessuna_azione 75%, chiudi 22%, mantieni_chiusa 3% |
| sala | 0.50 | 0 | 0 | 329.98 | nessuna_azione 67%, chiudi 22%, mantieni_chiusa 12% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0.40 | 0.40 | 0.40 | 0.20 | 0.20 |
| camera_grande | 0.50 | 0.50 | 0.50 | 0.30 | 0.20 |
| camera | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 |
| corridoio | 0.60 | 0.60 | 0.40 | 0.20 | 0.20 |
| bagno | 0.30 | 0.30 | 0.30 | 0.30 | 0.20 |
| sala | 0.50 | 0.50 | 0.50 | 0.30 | 0.20 |


**Soglie effettive quando consiglia 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):

_nessun dato_

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
| cucina | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| camera_grande | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| camera | 4 | 4 | 50 | 50 | 0 | 1 | override_rate(3): "0",100,50; consiglio_accuracy(3): "0",0,50; prediction_factor_humidity(2): "1.0",1.0; prediction_factor_temperature(2): "1.0",1.0; prediction | idle 1, open_override 1, prediction_checked 1, close_concordante 1 | 8 | 100 |
| corridoio | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| bagno | 4 | 4 | 50 | 50 | 0 | 1 | override_rate(3): "0",100,50; consiglio_accuracy(3): "0",0,50; prediction_factor_humidity(2): "1.0",1.0; prediction_factor_temperature(2): "1.0",1.0; prediction | idle 1, open_override 1, prediction_checked 1, close_concordante 1 | 8 | 100 |
| sala | 4 | 4 | 50 | 50 | 0 | 1 | override_rate(3): "0",100,50; consiglio_accuracy(3): "0",0,50; prediction_factor_humidity(2): "1.0",1.0; prediction_factor_temperature(2): "1.0",1.0; prediction | idle 1, open_override 1, prediction_checked 1, close_concordante 1 | 8 | 99.22 |

_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._

## 7. Efficacia delle aperture (osservata)

did = variazione di omega della stanza meno quella delle altre stanze con finestra chiusa (stesso intervallo). `eff_regola_RH` applica la regola attuale (RH scende >= 2 punti in 60 min), `eff_fisica` richiede did60 < -0.3 g/kg.


| gruppo | n | dur_med | con_impianto | dRH60_med | dOmega60_med | did60_med | n_did | eff_regola_RH_pct | eff_fisica_pct |
|---|---|---|---|---|---|---|---|---|---|
| tutte | 6 | 13.14 | 6 | - | - | - | 0 | - | - |
| dopo consiglio apri | 0 | - | 0 | - | - | - | 0 | - | - |
| senza consiglio | 6 | 13.14 | 6 | - | - | - | 0 | - | - |
| durata < 1 min | 0 | - | 0 | - | - | - | 0 | - | - |
| durata >= 5 min | 5 | 13.18 | 5 | - | - | - | 0 | - | - |
| durata >= 5 min e consiglio | 0 | - | 0 | - | - | - | 0 | - | - |
| durata >= 5 min senza consiglio | 5 | 13.18 | 5 | - | - | - | 0 | - | - |


**Previsione umidita' vs reale all'orizzonte** (n=6): errore mediano -6.75 punti RH, MAE 6.17, correlazione 0.35


**Ultime 30 aperture** (dRH in punti %, dOmega in g/kg):


| stanza | inizio | dur_min | fine | consiglio_apri_prima | impianto | t_ext | dw0 | dRH30 | dRH60 | dOmega30 | dOmega60 | did60 | n_ctrl60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | 10-29 14:39 | 1.93 | off | False | True | 22 | 0.48 | - | - | - | - | - | 0 |
| camera_grande | 10-29 14:19 | 13.02 | off | False | True | 22.10 | 1.14 | - | - | - | - | - | 0 |
| camera | 10-29 14:19 | 13.11 | off | False | True | 22.20 | 1.49 | - | - | - | - | - | 0 |
| bagno | 10-29 14:19 | 13.22 | off | False | True | 22.10 | 1.33 | - | - | - | - | - | 0 |
| sala | 10-29 14:19 | 13.22 | off | False | True | 22.10 | 1.90 | - | - | - | - | - | 0 |
| cucina | 10-29 14:18 | 13.18 | off | False | True | 22.10 | 2.88 | - | - | - | - | - | 0 |


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
| cucina | 12 | 5.50 | 6 | 0 | 12 | 0.21 | 0.22 |
| camera_grande | 12 | 3 | 11 | 0 | 12 | 0.21 | 0.21 |
| camera | 12 | 11.50 | 18.90 | 41.67 | 12 | 0.21 | 0.21 |
| corridoio | - | - | - | - | 12 | 0.19 | 0.21 |
| bagno | - | - | - | - | 12 | 0.21 | 0.21 |
| sala | - | - | - | - | 12 | 0.20 | 0.22 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=21.9, p10=22.2, p50=22.6, p90=22.9, max=23.1; RH_ext min=36, p10=37, p50=38, p90=39, max=47; omega_ext min=6.34, p10=6.60, p50=6.76, p90=6.99, max=8.26; fonti: clima_locale 286


**Pioggia:** 0.0% dei campioni > 0 (n=1).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 286 | 0 | 23.10 | 8.26 | 47 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| sensor.fancoil_sala_humidity | 1 | 1 | 0.03 | 0.03 | 10-29 14:11 | 0 | 14h:1 |
| sensor.umidita_sala_pilota | 1 | 1 | 0.03 | 0.03 | 10-29 14:11 | 0 | 14h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 16 | 16 | 16 | 2 | 2 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 13 | 13 | 13 | 1 | 1 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 39512; entita' del sistema clima (nome contiene stanza e sensore tipo): 11519 (29.2%)

| entita | righe |
|---|---|
| automation.fancoil_listener_eventi_log | 1172 |
| sensor.previsione_finestra_bagno | 836 |
| sensor.consumo_casa_rapido | 790 |
| sensor.previsione_finestra_cucina | 767 |
| sensor.statistics_temperatura_camera_grande_variance | 732 |
| sensor.statistics_temperatura_camera_variance | 732 |
| sensor.statistics_temperatura_bagno_variance | 730 |
| sensor.statistics_temperatura_sala_variance | 728 |
| sensor.consumo_impianto_nuovo | 691 |
| sensor.previsione_finestra_corridoio | 679 |
| sensor.previsione_finestra_sala | 642 |
| sensor.previsione_finestra_camera | 630 |
| sensor.potenza_carichi_non_misurati | 629 |
| sensor.previsione_finestra_camera_grande | 614 |
| sensor.corridoio_calibrazione_riepilogo | 551 |
| sensor.cucina_calibrazione_riepilogo | 482 |
| sensor.net_grid_power | 397 |
| sensor.prism_tensione_attuale | 387 |
| sensor.locale_tecnico_prism_power_grid_voltage | 387 |
| automation.ev_listener_eventi_log | 382 |
