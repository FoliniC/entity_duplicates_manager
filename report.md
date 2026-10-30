# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 07:53 a 2026-10-29 08:53 (Europe/Rome); righe lette: 3219; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.contact_cucina_contact_cucina | 0 | 0 | 0 | - |
| binary_sensor.contact_cucina_not_used | 0 | 0 | 0 | - |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_not_used | 0 | 0 | 0 | - |
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
| binary_sensor.wifi_garage_door_module_garage_contact | 0 | 0 | 0 | - |
| input_boolean.finestra_bagno_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_camera_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_cucina_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_sala_aperta | 0 | 0 | 0 | - |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 4 | 0 | 1217.55 | 50.03 | 51.50 | 52.97 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 4 | 0 | 1217.55 | 50.03 | 51.50 | 52.97 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 2 | 0 | 1552.83 | 50.04 | 52 | 53.96 | 0 | 0 | 0 | False | 4 |
| cucina | t_reale | 1 | 0 | - | 19.40 | 19.40 | 19.40 | 0 | 0 | 0 | False | - |
| cucina | t_fancoil | 1 | 0 | - | 19.40 | 19.40 | 19.40 | 0 | 0 | 0 | False | - |
| cucina | omega | 8 | 0 | 87.02 | 7.38 | 7.61 | 7.83 | 0 | 0 | 0 | False | 0.15 |
| camera_grande | rh_pilota | 3 | 0 | 916.67 | 52.02 | 53 | 53.98 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 3 | 0 | 916.67 | 52.02 | 53 | 53.98 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 1 | 0 | - | 50 | 50 | 50 | 0 | 0 | 0 | False | - |
| camera_grande | t_reale | 16 | 0 | 3.89 | 19 | 19.20 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 16 | 0 | 3.89 | 19 | 19.20 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 19 | 0 | 4.58 | 7.49 | 7.73 | 7.97 | 0 | 0 | 0 | False | 0.10 |
| camera | rh_pilota | 1 | 0 | - | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 1 | 0 | - | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_th | 1 | 0 | - | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 1 | 0 | - | 20.20 | 20.20 | 20.20 | 0 | 0 | 0 | False | - |
| camera | t_fancoil | 1 | 0 | - | 20.20 | 20.20 | 20.20 | 0 | 0 | 0 | False | - |
| camera | omega | 1 | 0 | - | 8.54 | 8.54 | 8.54 | 0 | 0 | 0 | False | - |
| corridoio | rh_pilota | 2 | 0 | 1769.39 | 49.01 | 49.50 | 49.99 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 2 | 0 | 1769.39 | 49.01 | 49.50 | 49.99 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 1 | 0 | - | 20.80 | 20.80 | 20.80 | 0 | 0 | 0 | False | - |
| corridoio | t_fancoil | 1 | 0 | - | 20.80 | 20.80 | 20.80 | 0 | 0 | 0 | False | - |
| corridoio | omega | 3 | 0 | 884.70 | 7.89 | 7.89 | 8.05 | 0 | 0 | 0 | False | 0.16 |
| bagno | rh_pilota | 3 | 0 | 1135.51 | 52.02 | 53 | 53.98 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 3 | 0 | 1135.51 | 52.02 | 53 | 53.98 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 3 | 0 | 1369.08 | 19.60 | 19.60 | 19.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 3 | 0 | 1369.08 | 19.60 | 19.60 | 19.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 7 | 0 | 602.69 | 7.78 | 8.07 | 8.17 | 0 | 0 | 0 | False | 0.10 |
| sala | rh_pilota | 1 | 0 | - | 56 | 56 | 56 | 0 | 0 | 0 | False | - |
| sala | rh_fancoil | 1 | 0 | - | 56 | 56 | 56 | 0 | 0 | 0 | False | - |
| sala | t_reale | 1 | 0 | - | 20.20 | 20.20 | 20.20 | 0 | 0 | 0 | False | - |
| sala | t_fancoil | 1 | 0 | - | 20.20 | 20.20 | 20.20 | 0 | 0 | 0 | False | - |
| sala | omega | 1 | 0 | - | 8.70 | 8.70 | 8.70 | 0 | 0 | 0 | False | - |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 0 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 0 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 3600.16 | nessuna_azione 100% |
| camera_grande | 0 | 0 | 0 | 3600.13 | nessuna_azione 100% |
| camera | 0 | 0 | 0 | 3600.49 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 3600.19 | nessuna_azione 100% |
| bagno | 0 | 0 | 0 | 3600.51 | nessuna_azione 100% |
| sala | 0 | 0 | 0 | 3600.37 | nessuna_azione 100% |


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
| cucina | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| camera_grande | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| camera | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| corridoio | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| bagno | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |
| sala | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 8 | 100 |

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
| cucina | 12 | 2 | 3 | 0 | 12 | 0.17 | 0.17 |
| camera_grande | 12 | 3.50 | 4 | 0 | 12 | 0.17 | 0.18 |
| camera | 12 | 9 | 9 | 0 | 12 | 0.19 | 0.19 |
| corridoio | - | - | - | - | 12 | 0.17 | 0.17 |
| bagno | - | - | - | - | 12 | 0.18 | 0.18 |
| sala | - | - | - | - | 12 | 0.19 | 0.19 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=9.6, p10=9.7, p50=9.9, p90=13.6, max=14.3; RH_ext min=55, p10=58, p50=67, p90=67, max=67; omega_ext min=5.18, p10=5.26, p50=5.34, p90=5.86, max=5.97; fonti: clima_locale 233


**Pioggia:** 0.0% dei campioni > 0 (n=1).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 233 | 0 | 14.30 | 5.97 | 67 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

_nessun dato_

## 9c. Contatto principale vs secondo ingresso ('not_used')

_nessun dato_

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 24537; entita' del sistema clima (nome contiene stanza e sensore tipo): 6730 (27.4%)

| entita | righe |
|---|---|
| sensor.statistics_temperatura_camera_variance | 732 |
| sensor.statistics_temperatura_sala_variance | 732 |
| sensor.statistics_temperatura_camera_grande_variance | 731 |
| sensor.statistics_temperatura_bagno_variance | 730 |
| sensor.consumo_impianto_nuovo | 632 |
| sensor.previsione_finestra_camera_grande | 461 |
| sensor.previsione_finestra_corridoio | 418 |
| sensor.previsione_finestra_bagno | 407 |
| sensor.previsione_finestra_sala | 398 |
| sensor.previsione_finestra_camera | 396 |
| sensor.previsione_finestra_cucina | 385 |
| automation.ev_listener_eventi_log | 366 |
| sensor.knx_interface_telegrams | 365 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 337 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 336 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 335 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 335 |
| sensor.smart_meter_2026_a_pdc_voltage_a | 325 |
| sensor.smart_meter_2026_a_pdc_total_power | 322 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_voltage_a | 318 |
