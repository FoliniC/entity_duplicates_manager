# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 19:35 a 2026-10-29 20:35 (Europe/Rome); righe lette: 2639; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.contact_cucina_contact_cucina | 6 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_cucina_not_used | 6 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 6 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_not_used | 6 | 0 | 0.99 | 0.01 |
| binary_sensor.finestracucina_alert | 6 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 9 | 1.00 | 0 | 0.00 |
| binary_sensor.finestracucina_motion | 6 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 9 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 3 | 0 | 1 | 0 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 3 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 3 | 0 | 1.00 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 3 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 3 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 9 | 0 | 0.99 | 0.01 |
| input_boolean.finestra_bagno_aperta | 3 | 0 | 1 | 0 |
| input_boolean.finestra_camera_aperta | 3 | 0 | 1.00 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 3 | 0 | 1 | 0 |
| input_boolean.finestra_cucina_aperta | 3 | 0 | 1.00 | 0 |
| input_boolean.finestra_sala_aperta | 3 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 5 | 0 | 913.85 | 52 | 52 | 53 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 8 | 0.58 | 268.19 | 52 | 52 | 53 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 5 | 0 | 1049.16 | 50 | 50 | 50.96 | 0 | 0 | 0 | False | 1 |
| cucina | t_reale | 28 | 0 | 7.91 | 21.40 | 21.50 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 30 | 0.58 | 7.50 | 21.40 | 21.40 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 57 | 0 | 2.82 | 8.70 | 8.80 | 8.86 | 0 | 0 | 0 | False | 0.10 |
| camera_grande | rh_pilota | 7 | 0 | 397.64 | 56 | 56 | 57 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 10 | 0.64 | 122.20 | 56 | 56 | 57 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 5 | 0 | 1037.85 | 50 | 50 | 51 | 0 | 0 | 0 | False | 1 |
| camera_grande | t_reale | 22 | 0 | 6.89 | 20.40 | 20.50 | 20.60 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 24 | 0.64 | 6.89 | 20.40 | 20.40 | 20.60 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 25 | 0 | 9.38 | 8.81 | 8.92 | 8.97 | 0 | 0 | 0 | False | 0.11 |
| camera | rh_pilota | 4 | 0 | 1120.66 | 53 | 53 | 53 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 7 | 0.60 | 489.84 | 53 | 53 | 53 | 0 | 0 | 0 | False | - |
| camera | rh_th | 4 | 0 | 1120.84 | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 4 | 0 | 1120.66 | 20.80 | 20.80 | 20.80 | 0 | 0 | 0 | False | - |
| camera | t_fancoil | 7 | 0.60 | 489.84 | 20.80 | 20.80 | 20.80 | 0 | 0 | 0 | False | - |
| camera | omega | 4 | 0 | 1120.68 | 8.54 | 8.54 | 8.54 | 0 | 0 | 0 | False | - |
| corridoio | rh_pilota | 4 | 0 | 1120.69 | 52 | 52 | 52 | 0 | 0 | 0 | False | - |
| corridoio | rh_fancoil | 7 | 0.58 | 489.83 | 52 | 52 | 52 | 0 | 0 | 0 | False | - |
| corridoio | t_reale | 4 | 0 | 1120.69 | 21.80 | 21.80 | 21.80 | 0 | 0 | 0 | False | - |
| corridoio | t_fancoil | 7 | 0.58 | 489.83 | 21.80 | 21.80 | 21.80 | 0 | 0 | 0 | False | - |
| corridoio | omega | 6 | 0 | 735.84 | 8.91 | 8.91 | 8.92 | 0 | 0 | 0 | False | 0.01 |
| bagno | rh_pilota | 8 | 0 | 182.31 | 55 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 10 | 0.62 | 177.91 | 55 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 67 | 0 | 5.81 | 20.60 | 20.80 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 70 | 0.62 | 6.23 | 20.60 | 20.80 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 71 | 0 | 6.28 | 8.87 | 8.92 | 9.03 | 0 | 0 | 0 | False | 0.11 |
| sala | rh_pilota | 4 | 0 | 1120.70 | 54 | 54 | 54 | 0 | 0 | 0 | False | - |
| sala | rh_fancoil | 8 | 0.55 | 8.28 | 54 | 54 | 54 | 0 | 0 | 0 | False | - |
| sala | t_reale | 8 | 0 | 24.10 | 21.20 | 21.40 | 21.40 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 11 | 0.49 | 16.72 | 21.20 | 21.40 | 21.40 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 13 | 0 | 16.71 | 8.92 | 9.03 | 9.04 | 0 | 0 | 0 | False | 0.11 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 0.55 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 0.52 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 3600 | nessuna_azione 100% |
| camera_grande | 0 | 0 | 0 | 3600 | nessuna_azione 100% |
| camera | 0 | 0 | 0 | 3600 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 3600 | nessuna_azione 100% |
| bagno | 0 | 0 | 0 | 3600 | nessuna_azione 100% |
| sala | 0 | 0 | 0 | 3600 | nessuna_azione 100% |


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
| cucina | 4 | 1 | 0 | 0 | 0 | 1.0 | - | idle 4 | 8 | 97.63 |
| camera_grande | 4 | 1 | 0 | 0 | 0 | 1.0 | - | idle 4 | 8 | 97.39 |
| camera | 4 | 1 | 0 | 0 | 0 | 1.0 | - | idle 4 | 8 | 95.89 |
| corridoio | 4 | 1 | 0 | 0 | 0 | 1.0 | - | idle 4 | 8 | 95.83 |
| bagno | 4 | 1 | 0 | 0 | 0 | 1.0 | - | idle 4 | 8 | 98.56 |
| sala | 4 | 1 | 0 | 0 | 0 | 1.0 | - | idle 4 | 8 | 95.80 |

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
| cucina | 13 | 2 | 3 | 0 | 13 | 0.19 | 0.20 |
| camera_grande | 13 | 6 | 6 | 0 | 13 | 0.20 | 0.20 |
| camera | 13 | 11 | 11 | 0 | 13 | 0.19 | 0.19 |
| corridoio | - | - | - | - | 13 | 0.19 | 0.20 |
| bagno | - | - | - | - | 13 | 0.20 | 0.20 |
| sala | - | - | - | - | 13 | 0.20 | 0.20 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=11.2, p10=11.2, p50=11.3, p90=11.6, max=11.8; RH_ext min=65, p10=65, p50=67, p90=67, max=67; omega_ext min=5.76, p10=5.76, p50=5.83, p90=5.86, max=5.89; fonti: clima_locale 86


**Pioggia:** 0.0% dei campioni > 0 (n=4).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 86 | 0 | 11.80 | 5.89 | 67 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 3 | 3 | 0.11 | 0.13 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| sensor.fancoil_cucina_humidity | 3 | 3 | 0.11 | 0.14 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 3 | 3 | 0.10 | 0.12 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| sensor.fancoil_camera_grande_humidity | 3 | 3 | 0.13 | 0.14 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| sensor.fancoil_camera_humidity | 3 | 3 | 0.11 | 0.15 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| sensor.fancoil_corridoio_humidity | 3 | 3 | 0.11 | 0.14 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| sensor.fancoil_bagno_humidity | 3 | 3 | 0.12 | 0.15 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| sensor.fancoil_sala_humidity | 3 | 3 | 0.11 | 0.14 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| binary_sensor.contact_cucina_not_used | 3 | 3 | 0.11 | 0.13 | 10-29 20:18 | 0 | 20h:2, 19h:1 |
| binary_sensor.finestra_camera_grande_not_used | 3 | 3 | 0.10 | 0.12 | 10-29 20:18 | 0 | 20h:2, 19h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 0 | 0 | 0 | 0 | 0 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 0 | 0 | 0 | 0 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 33248; entita' del sistema clima (nome contiene stanza e sensore tipo): 6098 (18.3%)

| entita | righe |
|---|---|
| automation.fancoil_listener_eventi_log | 706 |
| sensor.statistics_temperatura_sala_variance | 661 |
| sensor.statistics_temperatura_camera_variance | 660 |
| sensor.statistics_temperatura_bagno_variance | 659 |
| sensor.statistics_temperatura_camera_grande_variance | 657 |
| sensor.potenza_differenza_contatori | 654 |
| sensor.potenza_totale_bilancio | 627 |
| sensor.consumo_impianto_nuovo | 608 |
| sensor.consumo_casa_rapido | 608 |
| sensor.previsione_finestra_bagno | 415 |
| automation.ev_listener_eventi_log | 369 |
| sensor.knx_interface_telegrams | 359 |
| sensor.locale_tecnico_solarnet_power_battery_discharge | 356 |
| sensor.locale_tecnico_solarnet_power_load_consumed | 356 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 334 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 331 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 329 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 327 |
| sensor.smart_meter_2026_a_pdc_total_power | 326 |
| sensor.smart_meter_2026_a_pdc_voltage_a | 324 |
