# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 07:29 a 2026-10-29 08:59 (Europe/Rome); righe lette: 5331; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| cucina | rh_pilota | 6 | 0 | 781.86 | 49.05 | 51.50 | 55.85 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 5 | 0 | 1007.10 | 49.04 | 51 | 52.96 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 2 | 0 | 2992.83 | 50.04 | 52 | 53.96 | 0 | 0 | 0 | False | 4 |
| cucina | t_reale | 5 | 0 | 19.80 | 19.20 | 19.40 | 19.98 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 4 | 0 | 24.82 | 19.20 | 19.30 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 19 | 0 | 3.84 | 7.14 | 7.38 | 8.59 | 0 | 0 | 0 | False | 0.15 |
| camera_grande | rh_pilota | 5 | 0 | 1629.31 | 50.08 | 53 | 54.96 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 4 | 0 | 1875.74 | 52.03 | 53.50 | 54.97 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 2 | 0 | 17.24 | 50.04 | 52 | 53.96 | 0 | 0 | 0 | False | 4 |
| camera_grande | t_reale | 46 | 0 | 4.42 | 18 | 19 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 45 | 0 | 4.18 | 18 | 19 | 19.40 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 50 | 0 | 5.11 | 7.03 | 7.61 | 8.12 | 0 | 0 | 0 | False | 0.10 |
| camera | rh_pilota | 1 | 0 | - | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 1 | 0 | - | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_th | 1 | 0 | - | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 1 | 0 | - | 20.20 | 20.20 | 20.20 | 0 | 0 | 0 | False | - |
| camera | t_fancoil | 1 | 0 | - | 20.20 | 20.20 | 20.20 | 0 | 0 | 0 | False | - |
| camera | omega | 2 | 0 | 14.76 | 8.54 | 8.54 | 8.55 | 0 | 0 | 0 | False | 0.01 |
| corridoio | rh_pilota | 7 | 0 | 242.37 | 45.06 | 48 | 50.94 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 6 | 0 | 303.01 | 45.05 | 47.50 | 49.95 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 20 | 0 | 3.90 | 20.40 | 20.60 | 21.12 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 19 | 0 | 3.90 | 20.40 | 20.60 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 50 | 0 | 0.28 | 7.06 | 7.55 | 8.43 | 0 | 0 | 0 | False | 0.10 |
| bagno | rh_pilota | 5 | 0 | 845.39 | 51.04 | 53 | 56.88 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 4 | 0 | 1650.93 | 51.03 | 52.50 | 53.97 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 31 | 0 | 6.89 | 18.26 | 19.40 | 19.94 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 32 | 0 | 6.29 | 18.20 | 19.40 | 19.74 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 36 | 0 | 9.58 | 7.01 | 7.68 | 8.55 | 0 | 0 | 0 | False | 0.09 |
| sala | rh_pilota | 3 | 0 | 356.20 | 55.02 | 56 | 56 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 2 | 0 | 712.40 | 55.01 | 55.50 | 55.99 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 31 | 0 | 7.21 | 20.20 | 20.40 | 20.40 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 33 | 0 | 7.21 | 20.20 | 20.40 | 20.40 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 65 | 0 | 1.57 | 8.54 | 8.65 | 8.81 | 0 | 0 | 0 | False | 0.11 |

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
| cucina | 0.10 | 0 | 0 | 2700.08 | nessuna_azione 99%, apri 1% |
| camera_grande | 0.10 | 0 | 0 | 2700.07 | nessuna_azione 99%, apri 1% |
| camera | 0 | 0 | 0 | 5400.46 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 5400.17 | nessuna_azione 100% |
| bagno | 0.10 | 0 | 0 | 2700.25 | nessuna_azione 99%, apri 1% |
| sala | 0 | 0 | 0 | 5400.37 | nessuna_azione 100% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0.10 | 0.10 | 0.10 | 0 | 0 |
| camera_grande | 0.10 | 0.10 | 0.10 | 0 | 0 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0.10 | 0.10 | 0.10 | 0 | 0 |
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
| cucina | 1 | 1 | 1.00 | 0 | 0 | 1.11 |
| camera_grande | 1 | 1 | 1.00 | 0 | 0 | 1.11 |
| camera | 0 | 0 | - | 0 | - | 0 |
| bagno | 1 | 1 | 1.01 | 0 | 0 | 1.12 |
| sala | 0 | 0 | - | 0 | - | 0 |

_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._

## 9. Coerenza tra sensori

| stanza | pilota_vs_th_n | pilota_vs_th_p50 | pilota_vs_th_p95 | oltre15_pct | omega_n | omega_bias_med | omega_abs_p95 |
|---|---|---|---|---|---|---|---|
| cucina | 18 | 3 | 5 | 0 | 18 | 0.17 | 0.17 |
| camera_grande | 18 | 3 | 4 | 0 | 18 | 0.17 | 0.18 |
| camera | 18 | 9 | 9 | 0 | 18 | 0.19 | 0.19 |
| corridoio | - | - | - | - | 18 | 0.17 | 0.17 |
| bagno | - | - | - | - | 18 | 0.17 | 0.18 |
| sala | - | - | - | - | 18 | 0.19 | 0.19 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=9.6, p10=9.7, p50=10.0, p90=14.2, max=15.5; RH_ext min=53, p10=56, p50=66, p90=67, max=99; omega_ext min=5.13, p10=5.24, p50=5.34, p90=5.92, max=8.19; fonti: clima_locale 310


**Pioggia:** 0.0% dei campioni > 0 (n=1).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 310 | 0 | 15.50 | 8.19 | 99 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

_nessun dato_

## 9c. Contatto principale vs secondo ingresso ('not_used')

_nessun dato_

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 38876; entita' del sistema clima (nome contiene stanza e sensore tipo): 10863 (27.9%)

| entita | righe |
|---|---|
| sensor.statistics_temperatura_sala_variance | 1065 |
| sensor.statistics_temperatura_camera_variance | 1064 |
| sensor.statistics_temperatura_camera_grande_variance | 1063 |
| sensor.statistics_temperatura_bagno_variance | 1062 |
| sensor.consumo_impianto_nuovo | 940 |
| sensor.previsione_finestra_camera_grande | 729 |
| sensor.previsione_finestra_bagno | 669 |
| sensor.previsione_finestra_sala | 661 |
| sensor.previsione_finestra_corridoio | 644 |
| automation.ev_listener_eventi_log | 546 |
| sensor.previsione_finestra_cucina | 542 |
| sensor.knx_interface_telegrams | 541 |
| sensor.previsione_finestra_camera | 529 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 500 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 499 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 498 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 495 |
| sensor.smart_meter_2026_a_pdc_voltage_a | 480 |
| sensor.smart_meter_2026_a_pdc_total_power | 478 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_voltage_a | 474 |
