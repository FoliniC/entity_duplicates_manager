# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 19:19 a 2026-10-29 20:19 (Europe/Rome); righe lette: 2005; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.contact_cucina_contact_cucina | 4 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_cucina_not_used | 4 | 0 | 0.99 | 0.01 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 4 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_not_used | 4 | 0 | 0.99 | 0.01 |
| binary_sensor.finestracucina_alert | 4 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 6 | 1.00 | 0 | 0.00 |
| binary_sensor.finestracucina_motion | 4 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 6 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 2 | 0 | 1 | 0 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 2 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 2 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 2 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 2 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 6 | 0 | 0.99 | 0.01 |
| input_boolean.finestra_bagno_aperta | 2 | 0 | 1 | 0 |
| input_boolean.finestra_camera_aperta | 2 | 0 | 1 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 2 | 0 | 1 | 0 |
| input_boolean.finestra_cucina_aperta | 2 | 0 | 1 | 0 |
| input_boolean.finestra_sala_aperta | 2 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 4 | 0 | 1494.63 | 51.03 | 52 | 52 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 6 | 0.41 | 312.33 | 51.03 | 52 | 52 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 4 | 0 | 1131.42 | 50 | 50 | 50.97 | 0 | 0 | 0 | False | 1 |
| cucina | t_reale | 54 | 0 | 6.35 | 21.40 | 21.60 | 21.80 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 55 | 0.41 | 6.35 | 21.40 | 21.60 | 21.80 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 109 | 0 | 2.25 | 8.70 | 8.81 | 8.92 | 0 | 0 | 0 | False | 0.11 |
| camera_grande | rh_pilota | 4 | 0 | 1494.61 | 55.03 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 6 | 0.46 | 251.39 | 55.03 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 4 | 0 | 1494.67 | 50 | 50 | 50.97 | 0 | 0 | 0 | False | 1 |
| camera_grande | t_reale | 23 | 0 | 6.83 | 20.40 | 20.60 | 20.76 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 24 | 0.46 | 6.89 | 20.40 | 20.60 | 20.76 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 24 | 0 | 6.89 | 8.76 | 8.84 | 8.92 | 0 | 0 | 0 | False | 0.11 |
| camera | rh_pilota | 3 | 0 | 1787.64 | 53 | 53 | 53 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 5 | 0.42 | 747.93 | 53 | 53 | 53 | 0 | 0 | 0 | False | - |
| camera | rh_th | 3 | 0 | 1787.76 | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 14 | 0 | 7.98 | 20.80 | 20.80 | 21 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 16 | 0.42 | 7.98 | 20.80 | 20.80 | 21 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 14 | 0 | 7.98 | 8.54 | 8.54 | 8.65 | 0 | 0 | 0 | False | 0.11 |
| corridoio | rh_pilota | 4 | 0 | 1494.62 | 51.03 | 52 | 52 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 6 | 0.41 | 10.48 | 51.03 | 52 | 52 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 3 | 0 | 1787.65 | 21.80 | 21.80 | 21.80 | 0 | 0 | 0 | False | - |
| corridoio | t_fancoil | 5 | 0.41 | 747.63 | 21.80 | 21.80 | 21.80 | 0 | 0 | 0 | False | - |
| corridoio | omega | 7 | 0 | 203.65 | 8.74 | 8.91 | 8.92 | 0 | 0 | 0 | False | 0.01 |
| bagno | rh_pilota | 7 | 0 | 181.71 | 55 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 8 | 0.44 | 177.91 | 55 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 3 | 0 | 1787.63 | 20.80 | 20.80 | 20.80 | 0 | 0 | 0 | False | - |
| bagno | t_fancoil | 5 | 0.44 | 747.61 | 20.80 | 20.80 | 20.80 | 0 | 0 | 0 | False | - |
| bagno | omega | 7 | 0 | 181.73 | 8.87 | 9.03 | 9.03 | 0 | 0 | 0 | False | 0.16 |
| sala | rh_pilota | 4 | 0 | 1494.63 | 53.03 | 54 | 54 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 6 | 0.41 | 219.46 | 53.03 | 54 | 54 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 3 | 0 | 1787.67 | 21.40 | 21.40 | 21.40 | 0 | 0 | 0 | False | - |
| sala | t_fancoil | 5 | 0.41 | 747.68 | 21.40 | 21.40 | 21.40 | 0 | 0 | 0 | False | - |
| sala | omega | 5 | 0 | 857.04 | 8.87 | 9.04 | 9.04 | 0 | 0 | 0 | False | 0.17 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 0.39 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 0.38 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 3600.42 | nessuna_azione 100% |
| camera_grande | 0 | 0 | 0 | 3600.58 | nessuna_azione 100% |
| camera | 0 | 0 | 0 | 3600.32 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 3600.54 | nessuna_azione 100% |
| bagno | 0 | 0 | 0 | 3600.13 | nessuna_azione 100% |
| sala | 0 | 0 | 0 | 3600.16 | nessuna_azione 100% |


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
| cucina | 3 | 1 | 0 | 0 | 0 | 1.0 | - | idle 3 | 8 | 98.71 |
| camera_grande | 3 | 1 | 0 | 0 | 0 | 1.0 | - | idle 3 | 8 | 97.89 |
| camera | 3 | 1 | 0 | 0 | 0 | 1.0 | - | idle 3 | 8 | 97.33 |
| corridoio | 3 | 1 | 0 | 0 | 0 | 1.0 | - | idle 3 | 8 | 95.79 |
| bagno | 3 | 1 | 0 | 0 | 0 | 1.0 | - | idle 3 | 8 | 96.77 |
| sala | 3 | 1 | 0 | 0 | 0 | 1.0 | - | idle 3 | 8 | 95.56 |

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
| cucina | 12 | 2 | 2 | 0 | 12 | 0.19 | 0.20 |
| camera_grande | 12 | 6 | 6 | 0 | 12 | 0.20 | 0.20 |
| camera | 12 | 11 | 11 | 0 | 12 | 0.19 | 0.19 |
| corridoio | - | - | - | - | 12 | 0.20 | 0.20 |
| bagno | - | - | - | - | 12 | 0.20 | 0.20 |
| sala | - | - | - | - | 12 | 0.20 | 0.20 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=11.4, p10=11.5, p50=11.7, p90=11.8, max=11.9; RH_ext min=64, p10=65, p50=65, p90=66, max=66; omega_ext min=5.76, p10=5.76, p50=5.84, p90=5.88, max=5.92; fonti: clima_locale 54


**Pioggia:** 0.0% dei campioni > 0 (n=3).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 54 | 0 | 11.90 | 5.92 | 66 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 2 | 2 | 0.12 | 0.13 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| sensor.fancoil_cucina_humidity | 2 | 2 | 0.12 | 0.14 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 2 | 2 | 0.11 | 0.12 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| sensor.fancoil_camera_grande_humidity | 2 | 2 | 0.14 | 0.14 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| sensor.fancoil_camera_humidity | 2 | 2 | 0.13 | 0.15 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| sensor.fancoil_corridoio_humidity | 2 | 2 | 0.12 | 0.14 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| sensor.fancoil_bagno_humidity | 2 | 2 | 0.13 | 0.15 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| sensor.fancoil_sala_humidity | 2 | 2 | 0.12 | 0.14 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| binary_sensor.contact_cucina_not_used | 2 | 2 | 0.12 | 0.13 | 10-29 20:18 | 0 | 19h:1, 20h:1 |
| binary_sensor.finestra_camera_grande_not_used | 2 | 2 | 0.11 | 0.12 | 10-29 20:18 | 0 | 19h:1, 20h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 0 | 0 | 0 | 0 | 0 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 0 | 0 | 0 | 0 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 30452; entita' del sistema clima (nome contiene stanza e sensore tipo): 5502 (18.1%)

| entita | righe |
|---|---|
| automation.fancoil_listener_eventi_log | 892 |
| sensor.statistics_temperatura_camera_variance | 692 |
| sensor.statistics_temperatura_bagno_variance | 691 |
| sensor.statistics_temperatura_sala_variance | 691 |
| sensor.statistics_temperatura_camera_grande_variance | 690 |
| sensor.potenza_differenza_contatori | 662 |
| sensor.potenza_totale_bilancio | 633 |
| sensor.consumo_impianto_nuovo | 614 |
| sensor.consumo_casa_rapido | 614 |
| automation.ev_listener_eventi_log | 368 |
| sensor.knx_interface_telegrams | 361 |
| sensor.locale_tecnico_solarnet_power_battery_discharge | 358 |
| sensor.locale_tecnico_solarnet_power_load_consumed | 358 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 333 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 332 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 331 |
| sensor.smart_meter_2026_a_pdc_total_power | 328 |
| sensor.smart_meter_2026_a_pdc_voltage_a | 327 |
| sensor.smart_meter_2026_a_pdc_power_a | 325 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 324 |
