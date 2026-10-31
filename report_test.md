# Report diagnostico clima (v1.3)

Periodo: da 2026-10-30 10:47 a 2026-10-30 11:47 (Europe/Rome); righe lette: 2115; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.contact_cucina_contact_cucina | 8 | 0 | 0.98 | 0.02 |
| binary_sensor.contact_cucina_not_used | 8 | 0 | 0.98 | 0.02 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 8 | 0 | 0.99 | 0.01 |
| binary_sensor.finestra_camera_grande_not_used | 8 | 0 | 0.99 | 0.01 |
| binary_sensor.finestracucina_alert | 8 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 12 | 1.00 | 0 | 0.00 |
| binary_sensor.finestracucina_motion | 8 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 12 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 4 | 0 | 1 | 0 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 5 | 0 | 0.99 | 0.01 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 5 | 0 | 0.99 | 0.01 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 5 | 0 | 0.99 | 0.01 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 5 | 0 | 0.99 | 0.01 |
| binary_sensor.wifi_garage_door_module_garage_contact | 16 | 0.01 | 0.98 | 0.01 |
| input_boolean.finestra_bagno_aperta | 4 | 0 | 1 | 0 |
| input_boolean.finestra_camera_aperta | 4 | 0 | 1.00 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 4 | 0 | 1 | 0 |
| input_boolean.finestra_cucina_aperta | 4 | 0 | 1 | 0 |
| input_boolean.finestra_sala_aperta | 4 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 10 | 0 | 418.82 | 58 | 58.50 | 62.91 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 13 | 0.96 | 210.68 | 58 | 59 | 62.92 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 6 | 0 | 418.82 | 51 | 51 | 55.75 | 0 | 0 | 0 | False | 5 |
| cucina | t_reale | 25 | 0 | 9.59 | 18.40 | 20.20 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 29 | 0.97 | 9.15 | 18.40 | 20.20 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 57 | 0 | 3.95 | 8.53 | 9.31 | 10.07 | 0 | 0 | 0 | False | 0.12 |
| camera_grande | rh_pilota | 14 | 0 | 121.38 | 58.13 | 61 | 62 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 14 | 0.92 | 140.69 | 58.09 | 61.50 | 62 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 6 | 0 | 418.82 | 53 | 53 | 53.95 | 0 | 0 | 0 | False | 1 |
| camera_grande | t_reale | 19 | 0 | 141.12 | 13.20 | 19.60 | 21 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 24 | 0.92 | 85.33 | 13.20 | 19.50 | 21 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 28 | 0 | 60.57 | 6.14 | 9.14 | 9.50 | 0 | 0 | 0 | False | 0.15 |
| camera | rh_pilota | 6 | 0 | 426.51 | 53.05 | 54 | 54 | 0 | 0 | 0 | False | 1 |
| camera | rh_fancoil | 10 | 0.85 | 141.11 | 53.05 | 54 | 54 | 0 | 0 | 0 | False | 1 |
| camera | rh_th | 5 | 0 | 422.67 | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 16 | 0 | 151.02 | 19.80 | 20.30 | 21 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 19 | 0.85 | 125.08 | 19.80 | 20.40 | 21 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 18 | 0 | 151.02 | 7.82 | 8.43 | 8.68 | 0 | 0 | 0 | False | 0.11 |
| corridoio | rh_pilota | 8 | 0 | 239.82 | 54.07 | 55 | 56 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 11 | 0.82 | 163.96 | 54.06 | 55 | 56 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 18 | 0 | 8.61 | 20.40 | 20.60 | 21 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 22 | 0.82 | 8.11 | 20.40 | 20.60 | 21 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 39 | 0 | 3.34 | 8.30 | 8.79 | 9.13 | 0 | 0 | 0 | False | 0.12 |
| bagno | rh_pilota | 16 | 0 | 184.39 | 54.15 | 60 | 61 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 17 | 0.91 | 162.70 | 54.12 | 60 | 61 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 33 | 0 | 78.20 | 19.40 | 21.40 | 22.60 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 37 | 0.91 | 60.87 | 19.40 | 21.40 | 22.60 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 45 | 0 | 61.46 | 8.60 | 9.60 | 9.83 | 0 | 0 | 0 | False | 0.12 |
| sala | rh_pilota | 14 | 0 | 243.39 | 53.13 | 56 | 57 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 17 | 0.80 | 162.55 | 53.12 | 56 | 57 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 22 | 0 | 90.25 | 20.40 | 20.90 | 22.20 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 26 | 0.80 | 10.88 | 20.40 | 20.90 | 22.20 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 58 | 0 | 2.84 | 8.60 | 9.18 | 9.48 | 0 | 0 | 0 | False | 0.12 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 0 | - | - | 0 | 1.38 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 0 | - | - | 0 | 1.15 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 0 | - | - | 0 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 3600.09 | nessuna_azione 100% |
| camera_grande | 0 | 0 | 0 | 3600.36 | nessuna_azione 100% |
| camera | 0 | 0 | 0 | 3600.26 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 3600.25 | nessuna_azione 100% |
| bagno | 0 | 0 | 0 | 3600.22 | nessuna_azione 100% |
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
| cucina | 5 | 1 | 0 | 0 | 0 | 1.0 | - | idle 5 | 5 | 0 |
| camera_grande | 5 | 1 | 0 | 0 | 0 | 1.0 | - | idle 5 | 5 | 0 |
| camera | 5 | 1 | 0 | 0 | 0 | 1.0 | - | idle 5 | 5 | 0 |
| corridoio | 5 | 1 | 0 | 0 | 0 | 1.0 | - | idle 5 | 5 | 0 |
| bagno | 5 | 1 | 0 | 0 | 0 | 1.0 | - | idle 5 | 5 | 0 |
| sala | 5 | 1 | 0 | 0 | 0 | 1.0 | - | idle 5 | 5 | 0 |

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
| cucina | 12 | 6.50 | 7.45 | 0 | 12 | 0.18 | 0.21 |
| camera_grande | 12 | 8 | 9 | 0 | 12 | 0.19 | 0.19 |
| camera | 12 | 10 | 11 | 0 | 12 | 0.17 | 0.18 |
| corridoio | - | - | - | - | 12 | 0.18 | 0.19 |
| bagno | - | - | - | - | 12 | 0.19 | 0.20 |
| sala | - | - | - | - | 12 | 0.19 | 0.19 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=16.9, p10=17.3, p50=18.0, p90=18.5, max=18.7; RH_ext min=41, p10=41, p50=42, p90=44, max=46; omega_ext min=5.29, p10=5.62, p50=5.71, p90=5.84, max=6.05; fonti: clima_locale 186


**Pioggia:** 0.0% dei campioni > 0 (n=5).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 186 | 0 | 18.70 | 6.05 | 46 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 4 | 4 | 0.21 | 0.29 | 10-30 11:10 | 0 | 11h:4 |
| sensor.fancoil_cucina_humidity | 4 | 4 | 0.15 | 0.17 | 10-30 11:07 | 0 | 11h:4 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 4 | 4 | 0.18 | 0.23 | 10-30 11:10 | 0 | 11h:4 |
| sensor.fancoil_camera_grande_humidity | 4 | 4 | 0.14 | 0.15 | 10-30 11:07 | 0 | 11h:4 |
| sensor.fancoil_camera_humidity | 4 | 4 | 0.13 | 0.14 | 10-30 11:07 | 0 | 11h:4 |
| sensor.fancoil_corridoio_humidity | 4 | 4 | 0.12 | 0.14 | 10-30 11:07 | 0 | 11h:4 |
| sensor.fancoil_bagno_humidity | 4 | 4 | 0.14 | 0.16 | 10-30 11:07 | 0 | 11h:4 |
| sensor.fancoil_sala_humidity | 4 | 4 | 0.12 | 0.14 | 10-30 11:07 | 0 | 11h:4 |
| binary_sensor.contact_cucina_not_used | 4 | 4 | 0.21 | 0.29 | 10-30 11:10 | 0 | 11h:4 |
| binary_sensor.finestra_camera_grande_not_used | 4 | 4 | 0.18 | 0.23 | 10-30 11:10 | 0 | 11h:4 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 0 | 0 | 0 | 0 | 0 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 0 | 0 | 0 | 0 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 44135; entita' del sistema clima (nome contiene stanza e sensore tipo): 3559 (8.1%)

| entita | righe |
|---|---|
| sensor.consumo_casa_rapido | 1364 |
| sensor.prism_tensione_attuale | 1190 |
| sensor.locale_tecnico_prism_power_grid_voltage | 1186 |
| sensor.consumo_impianto_nuovo | 987 |
| sensor.net_grid_power | 958 |
| sensor.potenza_totale_bilancio | 861 |
| sensor.potenza_differenza_contatori | 856 |
| sensor.potenza_carichi_non_misurati | 615 |
| sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_voltaggio | 445 |
| sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_potenza | 431 |
| sensor.prism_potenza | 389 |
| sensor.locale_tecnico_prism_power_provided_to_car | 385 |
| sensor.prism_potenza_kw | 381 |
| sensor.wifi_digital_meter_2_induzione_wifi_digital_meter_2_induzione_voltage | 353 |
| sensor.knx_interface_telegrams | 353 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 332 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 332 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 330 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_b | 330 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 330 |
