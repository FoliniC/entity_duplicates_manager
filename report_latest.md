# Report diagnostico clima (v1.3)

Periodo: da 2026-10-30 11:27 a 2026-10-30 11:57 (Europe/Rome); righe lette: 1163; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.wifi_garage_door_module_garage_contact | 4 | 0.02 | 0.98 | 0 |
| input_boolean.finestra_bagno_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_camera_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_cucina_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_sala_aperta | 0 | 0 | 0 | - |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 4 | 0 | 429.32 | 60.03 | 61.50 | 62.97 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 4 | 0 | 429.32 | 60.03 | 61.50 | 62.97 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 1 | 0 | - | 56 | 56 | 56 | 0 | 0 | 0 | False | - |
| cucina | t_reale | 11 | 0 | 8.97 | 18.40 | 20.60 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 11 | 0 | 8.97 | 18.40 | 20.60 | 20.80 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 28 | 0 | 0.10 | 8.60 | 9.88 | 10.17 | 0 | 0 | 0 | False | 0.14 |
| camera_grande | rh_pilota | 6 | 0 | 120.26 | 57 | 58 | 59.95 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 6 | 0 | 120.26 | 57 | 58 | 59.95 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 1 | 0 | - | 54 | 54 | 54 | 0 | 0 | 0 | False | - |
| camera_grande | t_reale | 9 | 0 | 103.40 | 20.42 | 21 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 9 | 0 | 103.40 | 20.42 | 21 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 14 | 0 | 64.55 | 9.28 | 9.45 | 9.58 | 0 | 0 | 0 | False | 0.12 |
| camera | rh_pilota | 2 | 0 | 437.99 | 53.01 | 53.50 | 53.99 | 0 | 0 | 0 | False | 1 |
| camera | rh_fancoil | 2 | 0 | 437.98 | 53.01 | 53.50 | 53.99 | 0 | 0 | 0 | False | 1 |
| camera | rh_th | 1 | 0 | - | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 15 | 0 | 9.11 | 20.43 | 21 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 15 | 0 | 9.11 | 20.43 | 21 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 17 | 0 | 10.34 | 8.49 | 8.64 | 8.75 | 0 | 0 | 0 | False | 0.11 |
| corridoio | rh_pilota | 2 | 0 | 1331.66 | 56.01 | 56.50 | 56.99 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 2 | 0 | 1331.66 | 56.01 | 56.50 | 56.99 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 18 | 0 | 7.74 | 20.60 | 21 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 18 | 0 | 7.74 | 20.60 | 21 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 37 | 0 | 1.16 | 8.91 | 9.30 | 9.41 | 0 | 0 | 0 | False | 0.11 |
| bagno | rh_pilota | 6 | 0 | 125.23 | 54.05 | 56.50 | 58.95 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 6 | 0 | 125.24 | 54.05 | 56.50 | 58.95 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 30 | 0 | 8.76 | 21 | 22.50 | 22.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 30 | 0 | 8.76 | 21 | 22.50 | 22.80 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 35 | 0 | 12.81 | 9.59 | 9.72 | 9.84 | 0 | 0 | 0 | False | 0.12 |
| sala | rh_pilota | 4 | 0 | 117.25 | 53.03 | 54 | 54.97 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 4 | 0 | 117.25 | 53.03 | 54 | 54.97 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 19 | 0 | 6.08 | 21.64 | 22.20 | 22.40 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 19 | 0 | 6.08 | 21.64 | 22.20 | 22.40 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 43 | 0 | 1.15 | 9.25 | 9.48 | 9.60 | 0 | 0 | 0 | False | 0.12 |

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
| cucina | 0.10 | 0 | 0 | 900.04 | nessuna_azione 87%, apri 13% |
| camera_grande | 0 | 0 | 0 | 1800.36 | nessuna_azione 100% |
| camera | 0 | 0 | 0 | 1800.25 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 1800.23 | nessuna_azione 100% |
| bagno | 0 | 0 | 0 | 1800.22 | nessuna_azione 100% |
| sala | 0 | 0 | 0 | 1800.16 | nessuna_azione 100% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0.10 | 0.10 | 0.10 | 0.10 | 0 |
| camera_grande | 0 | 0 | 0 | 0 | 0 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0 | 0 | 0 | 0 | 0 |
| sala | 0 | 0 | 0 | 0 | 0 |


**Soglie effettive quando consiglia 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):

| stanza | impianto | ore_apri | dw_min_grezzo | dw_min_stabile30s | dw_p10_t | dw_p50_t | calo_min_stab | calo_p50_t |
|---|---|---|---|---|---|---|---|---|
| cucina | True | 0.07 | 4.10 | 4.14 | 4.14 | 4.21 | 18.70 | 18.80 |

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
| cucina | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 5 | 0 |
| camera_grande | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 5 | 0 |
| camera | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 5 | 0 |
| corridoio | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 5 | 0 |
| bagno | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 5 | 0 |
| sala | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 5 | 0 |

_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._


## 7. Efficacia delle aperture (osservata)

_Nessuna apertura finestra nel periodo: impossibile valutare efficacia._


## 8. Consigli 'apri' (episodi >= 60 s) seguiti da un'apertura entro 15 min

| stanza | episodi_apri_tot | episodi_ge60s | durata_med_min | seguiti | seguiti_pct | tempo_in_apri_pct |
|---|---|---|---|---|---|---|
| cucina | 1 | 1 | 4.00 | 0 | 0 | 13.33 |
| camera_grande | 0 | 0 | - | 0 | - | 0 |
| camera | 0 | 0 | - | 0 | - | 0 |
| bagno | 0 | 0 | - | 0 | - | 0 |
| sala | 0 | 0 | - | 0 | - | 0 |

_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._

## 9. Coerenza tra sensori

| stanza | pilota_vs_th_n | pilota_vs_th_p50 | pilota_vs_th_p95 | oltre15_pct | omega_n | omega_bias_med | omega_abs_p95 |
|---|---|---|---|---|---|---|---|
| cucina | 6 | 6 | 7 | 0 | 6 | 0.21 | 0.21 |
| camera_grande | 6 | 4 | 4.75 | 0 | 6 | 0.19 | 0.20 |
| camera | 6 | 11 | 11 | 0 | 6 | 0.18 | 0.18 |
| corridoio | - | - | - | - | 6 | 0.19 | 0.19 |
| bagno | - | - | - | - | 6 | 0.20 | 0.20 |
| sala | - | - | - | - | 6 | 0.19 | 0.20 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=17.8, p10=18.0, p50=18.5, p90=18.8, max=19.1; RH_ext min=41, p10=41, p50=42, p90=43, max=43; omega_ext min=5.52, p10=5.65, p50=5.80, p90=6.01, max=6.06; fonti: clima_locale 151


**Pioggia:** 0.0% dei campioni > 0 (n=1).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 151 | 0 | 19.10 | 6.06 | 43 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

_nessun dato_

## 9c. Contatto principale vs secondo ingresso ('not_used')

_nessun dato_

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 20114; entita' del sistema clima (nome contiene stanza e sensore tipo): 1691 (8.4%)

| entita | righe |
|---|---|
| sensor.consumo_casa_rapido | 1000 |
| sensor.potenza_differenza_contatori | 962 |
| sensor.potenza_totale_bilancio | 934 |
| sensor.net_grid_power | 773 |
| sensor.locale_tecnico_prism_power_grid_voltage | 656 |
| sensor.prism_tensione_attuale | 656 |
| sensor.consumo_impianto_nuovo | 536 |
| sensor.prism_potenza | 464 |
| sensor.prism_potenza_kw | 464 |
| sensor.locale_tecnico_prism_power_provided_to_car | 464 |
| sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_voltaggio | 219 |
| sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_potenza | 205 |
| sensor.knx_interface_telegrams | 181 |
| sensor.locale_tecnico_solarnet_power_battery_discharge | 179 |
| sensor.locale_tecnico_solarnet_power_load_consumed | 179 |
| sensor.wifi_digital_meter_2_induzione_wifi_digital_meter_2_induzione_voltage | 175 |
| sensor.ev_charging_status_markdown | 175 |
| automation.log_ev_charging_reason_changes | 174 |
| sensor.smart_meter_2026_a_pdc_power_a | 170 |
| sensor.locale_tecnico_solarnet_power_grid_import | 170 |
