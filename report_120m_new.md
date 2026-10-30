# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 08:20 a 2026-10-29 10:20 (Europe/Rome); righe lette: 10470; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.contact_cucina_contact_cucina | 10 | 0 | 0.97 | 0.03 |
| binary_sensor.contact_cucina_not_used | 10 | 0 | 0.97 | 0.03 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 10 | 0 | 0.97 | 0.03 |
| binary_sensor.finestra_camera_grande_not_used | 10 | 0 | 0.97 | 0.03 |
| binary_sensor.finestracucina_alert | 10 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 15 | 1.00 | 0 | 0.00 |
| binary_sensor.finestracucina_motion | 10 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 15 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 5 | 0 | 1 | 0 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 5 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 5 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 5 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 5 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 15 | 0 | 0.98 | 0.02 |
| input_boolean.finestra_bagno_aperta | 5 | 0 | 1.00 | 0 |
| input_boolean.finestra_camera_aperta | 5 | 0 | 1 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 5 | 0 | 1 | 0 |
| input_boolean.finestra_cucina_aperta | 5 | 0 | 1 | 0 |
| input_boolean.finestra_sala_aperta | 5 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 8 | 0 | 598.40 | 52.07 | 54 | 54 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 13 | 0.63 | 372.26 | 52.07 | 54 | 54 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 7 | 0 | 586.12 | 50.06 | 51 | 51 | 0 | 0 | 0 | False | 1 |
| cucina | t_reale | 127 | 0 | 6.43 | 19.40 | 19.60 | 19.60 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 132 | 0.63 | 6.47 | 19.40 | 19.60 | 19.60 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 253 | 0 | 1.75 | 7.82 | 7.92 | 8.07 | 0 | 0 | 0 | False | 0.10 |
| camera_grande | rh_pilota | 9 | 0 | 505.79 | 53.08 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 14 | 0.59 | 317.76 | 53.08 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 8 | 0 | 437.80 | 50 | 50 | 51 | 0 | 0 | 0 | False | 1 |
| camera_grande | t_reale | 156 | 0 | 4.98 | 19.20 | 19.20 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 161 | 0.59 | 5.06 | 19.20 | 19.20 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 160 | 0 | 5.01 | 7.87 | 8.02 | 8.16 | 0 | 0 | 0 | False | 0.10 |
| camera | rh_pilota | 6 | 0 | 574.23 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 11 | 0.53 | 165.08 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_th | 6 | 0 | 573.99 | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 45 | 0 | 9.36 | 20 | 20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 50 | 0.53 | 9.02 | 20 | 20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 46 | 0 | 9.03 | 8.43 | 8.43 | 8.54 | 0 | 0 | 0 | False | 0.11 |
| corridoio | rh_pilota | 10 | 0.10 | 320.51 | 49.08 | 51 | 51 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 15 | 0.69 | 153.93 | 49.08 | 51 | 51 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 71 | 0 | 8.30 | 20.42 | 20.80 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 78 | 0.69 | 6.81 | 20.60 | 20.60 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 144 | 0.10 | 1.78 | 7.81 | 8.11 | 8.21 | 0 | 0 | 0 | False | 0.11 |
| bagno | rh_pilota | 8 | 0 | 598.47 | 53.07 | 55 | 55 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 13 | 0.58 | 372.76 | 53.07 | 55 | 55 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 8 | 0 | 574.25 | 19.60 | 19.60 | 19.79 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 13 | 0.58 | 164.72 | 19.60 | 19.60 | 19.79 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 11 | 0 | 579.75 | 7.93 | 8.22 | 8.22 | 0 | 0 | 0 | False | 0.10 |
| sala | rh_pilota | 8 | 0 | 598.38 | 54 | 54 | 55.93 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 13 | 0.64 | 371.80 | 54 | 54 | 55.93 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 29 | 0 | 17.97 | 20.20 | 21.40 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 32 | 0.64 | 9.56 | 20.20 | 21.40 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 56 | 0 | 2.82 | 8.65 | 8.92 | 9.14 | 0 | 0 | 0 | False | 0.11 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 0.92 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 0.75 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 7200.15 | nessuna_azione 100% |
| camera_grande | 0 | 0 | 0 | 7200.28 | nessuna_azione 100% |
| camera | 0 | 0 | 0 | 7200.49 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 7200.26 | nessuna_azione 100% |
| bagno | 0 | 0 | 0 | 7200.06 | nessuna_azione 100% |
| sala | 0 | 0 | 0 | 7200.17 | nessuna_azione 100% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 0 | 0 |
| camera_grande | 0 | 0 | 0 | 0 | 0 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0 | 0 | 0 | 0 | 0 |
| sala | 0 | 0 | 0 | 0 | 0 |


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
| cucina | 6 | 1 | 0 | 0 | 0 | 1.0 | - | idle 6 | 8 | 99.26 |
| camera_grande | 6 | 1 | 0 | 0 | 0 | 1.0 | - | idle 6 | 8 | 99.30 |
| camera | 6 | 1 | 0 | 0 | 0 | 1.0 | - | idle 6 | 8 | 98.98 |
| corridoio | 6 | 1 | 0 | 0 | 0 | 1.0 | - | idle 6 | 8 | 98.61 |
| bagno | 6 | 1 | 0 | 0 | 0 | 1.0 | - | idle 6 | 8 | 98.87 |
| sala | 6 | 1 | 0 | 0 | 0 | 1.0 | - | idle 6 | 8 | 98.90 |

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
| cucina | 25 | 3 | 3 | 0 | 25 | 0.17 | 0.17 |
| camera_grande | 25 | 5 | 6 | 0 | 25 | 0.17 | 0.18 |
| camera | 25 | 9 | 9 | 0 | 25 | 0.18 | 0.19 |
| corridoio | - | - | - | - | 25 | 0.17 | 0.18 |
| bagno | - | - | - | - | 25 | 0.17 | 0.18 |
| sala | - | - | - | - | 25 | 0.19 | 0.19 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=9.9, p10=11.3, p50=17.3, p90=19.2, max=20.0; RH_ext min=41, p10=44, p50=50, p90=64, max=67; omega_ext min=5.29, p10=5.63, p50=6.35, p90=6.62, max=6.82; fonti: clima_locale 464


**Pioggia:** 0.0% dei campioni > 0 (n=6).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 464 | 0 | 20 | 6.82 | 67 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 5 | 5 | 0.25 | 0.43 | 10-29 10:02 | 0 | 10h:3, 9h:2 |
| sensor.fancoil_cucina_humidity | 5 | 5 | 0.14 | 0.21 | 10-29 09:52 | 0 | 10h:3, 9h:2 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 5 | 5 | 0.19 | 0.36 | 10-29 10:02 | 0 | 10h:3, 9h:2 |
| sensor.fancoil_camera_grande_humidity | 5 | 5 | 0.13 | 0.20 | 10-29 10:02 | 0 | 10h:3, 9h:2 |
| sensor.fancoil_camera_humidity | 5 | 5 | 0.13 | 0.19 | 10-29 09:52 | 0 | 10h:3, 9h:2 |
| sensor.fancoil_corridoio_humidity | 6 | 6 | 0.13 | 0.20 | 10-29 09:52 | 0 | 9h:3, 10h:3 |
| sensor.umidita_corridoio_pilota | 1 | 1 | 0.12 | 0.12 | 10-29 09:48 | 0 | 9h:1 |
| sensor.fancoil_bagno_humidity | 5 | 5 | 0.13 | 0.19 | 10-29 10:02 | 0 | 10h:3, 9h:2 |
| sensor.fancoil_sala_humidity | 5 | 5 | 0.14 | 0.20 | 10-29 09:52 | 0 | 10h:3, 9h:2 |
| binary_sensor.contact_cucina_not_used | 5 | 5 | 0.25 | 0.43 | 10-29 10:02 | 0 | 10h:3, 9h:2 |
| binary_sensor.finestra_camera_grande_not_used | 5 | 5 | 0.19 | 0.36 | 10-29 10:02 | 0 | 10h:3, 9h:2 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 0 | 0 | 0 | 0 | 0 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 0 | 0 | 0 | 0 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 72202; entita' del sistema clima (nome contiene stanza e sensore tipo): 18035 (25.0%)

| entita | righe |
|---|---|
| automation.fancoil_listener_eventi_log | 2281 |
| sensor.previsione_finestra_camera_grande | 1430 |
| sensor.previsione_finestra_cucina | 1348 |
| sensor.statistics_temperatura_camera_variance | 1323 |
| sensor.statistics_temperatura_sala_variance | 1317 |
| sensor.statistics_temperatura_bagno_variance | 1316 |
| sensor.statistics_temperatura_camera_grande_variance | 1316 |
| sensor.consumo_impianto_nuovo | 1198 |
| sensor.previsione_finestra_corridoio | 1076 |
| sensor.previsione_finestra_camera | 980 |
| sensor.previsione_finestra_sala | 905 |
| sensor.previsione_finestra_bagno | 881 |
| automation.ev_listener_eventi_log | 737 |
| sensor.knx_interface_telegrams | 709 |
| sensor.cucina_calibrazione_riepilogo | 703 |
| sensor.locale_tecnico_solarnet_power_battery_charge | 702 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 658 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 657 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 646 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 645 |
