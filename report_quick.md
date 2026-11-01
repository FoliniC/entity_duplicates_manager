# Report diagnostico clima (v1.3)

Periodo: da 2026-10-31 11:33 a 2026-10-31 11:43 (Europe/Rome); righe lette: 729; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 1 | 0 | 1 | 0 |
| binary_sensor.finestra_camera_grande_not_used | 1 | 0 | 1 | 0 |
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
| input_boolean.finestra_bagno_aperta | 1 | 0 | 1 | 0 |
| input_boolean.finestra_camera_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_cucina_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_sala_aperta | 1 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 2 | 0 | 234.57 | 45.01 | 45.50 | 45.99 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 2 | 0 | 234.57 | 45.01 | 45.50 | 45.99 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 1 | 0 | - | 48 | 48 | 48 | 0 | 0 | 0 | False | - |
| cucina | t_reale | 15 | 0 | 5.19 | 19.80 | 20 | 20 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 15 | 0 | 5.19 | 19.80 | 20 | 20 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 31 | 0 | 1.15 | 6.79 | 6.88 | 7.03 | 0 | 0 | 0 | False | 0.09 |
| camera_grande | rh_pilota | 6 | 0 | 60.17 | 39 | 40 | 40.95 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_fancoil | 6 | 0 | 60.17 | 39 | 40 | 40.95 | 0 | 0 | 0 | False | 1 |
| camera_grande | rh_th | 1 | 0 | - | 45 | 45 | 45 | 0 | 0 | 0 | False | - |
| camera_grande | t_reale | 7 | 0 | 64.50 | 19.21 | 19.60 | 20.19 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 7 | 0 | 64.50 | 19.21 | 19.60 | 20.19 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 12 | 0 | 41.38 | 5.67 | 5.92 | 6.32 | 0 | 0 | 0 | False | 0.08 |
| camera | rh_pilota | 8 | 0 | 61.03 | 42.07 | 44 | 45 | 0 | 0 | 0 | False | 1 |
| camera | rh_fancoil | 8 | 0 | 61.03 | 42.07 | 44 | 45 | 0 | 0 | 0 | False | 1 |
| camera | rh_th | 1 | 0 | - | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 8 | 0 | 66.89 | 19.21 | 19.90 | 20.59 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 8 | 0 | 66.89 | 19.21 | 19.90 | 20.59 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 15 | 0 | 30.51 | 6.19 | 6.64 | 7.12 | 0 | 0 | 0 | False | 0.12 |
| corridoio | rh_pilota | 7 | 0 | 91.22 | 36.06 | 38 | 38.94 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 7 | 0 | 91.22 | 36.06 | 38 | 38.94 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 10 | 0 | 6.53 | 19.60 | 19.80 | 20.18 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 10 | 0 | 6.52 | 19.60 | 19.80 | 20.18 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 31 | 0 | 1.16 | 5.41 | 5.73 | 5.95 | 0 | 0 | 0 | False | 0.07 |
| bagno | rh_pilota | 5 | 0 | 90.32 | 36.04 | 37 | 38 | 0 | 0 | 0 | False | 1 |
| bagno | rh_fancoil | 5 | 0 | 90.32 | 36.04 | 37 | 38 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 5 | 0 | 57.90 | 21.81 | 22 | 22.20 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 5 | 0 | 57.90 | 21.81 | 22 | 22.20 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 9 | 0 | 23.46 | 6.15 | 6.57 | 6.65 | 0 | 0 | 0 | False | 0.12 |
| sala | rh_pilota | 7 | 0 | 61.19 | 36.06 | 38 | 39.94 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 7 | 0 | 61.19 | 36.06 | 38 | 39.94 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 12 | 0 | 44.00 | 20.22 | 21.30 | 22.38 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 12 | 0 | 44.00 | 20.22 | 21.30 | 22.38 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 35 | 0 | 3.00 | 5.99 | 6.31 | 6.53 | 0 | 0 | 0 | False | 0.08 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 1 | 10 | 10 | 100 | 0 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 1 | 6.16 | 6.16 | 61.63 | 0 |
| camera | input_boolean.finestra_camera_aperta | 1 | 10 | 10 | 100 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 1 | 0.72 | 0.72 | 7.21 | 0 |
| sala | input_boolean.finestra_sala_aperta | 1 | 6.62 | 6.62 | 66.16 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 600.19 | mantieni_aperta 100% |
| camera_grande | 0.10 | 0 | 0 | 300.18 | mantieni_aperta 70%, mantieni_chiusa 30% |
| camera | 0 | 0 | 0 | 600.26 | mantieni_aperta 100% |
| corridoio | 0 | 0 | 0 | 600.46 | nessuna_azione 100% |
| bagno | 0.10 | 0 | 0 | 300.04 | nessuna_azione 90%, mantieni_aperta 10% |
| sala | 0.10 | 0 | 0 | 300.21 | mantieni_aperta 70%, mantieni_chiusa 30% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0 | 0 | 0 | 0 | 0 |
| camera_grande | 0.10 | 0.10 | 0.10 | 0.10 | 0 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0.10 | 0.10 | 0.10 | 0 | 0 |
| sala | 0.10 | 0.10 | 0.10 | 0.10 | 0 |


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
| cucina | 1 | 1 | 100 | 0 | 0 | 1 | - | prediction_checked 1 | 8 | 100 |
| camera_grande | 2 | 2 | 50 | 50 | 0 | 1 | override_rate(2): 100,50; consiglio_accuracy(2): 0,50; last_prediction_valid(2): "",false; last_prediction_reason(2): "azione_chiusura_senza_previsi,"finestra_c | prediction_checked 1, close_concordante 1 | 8 | 75 |
| camera | 1 | 1 | 100 | 0 | 0 | 1 | - | prediction_checked 1 | 8 | 100 |
| corridoio | 1 | 1 | 0 | 0 | 0 | 1.0 | - | idle 1 | 5 | 0 |
| bagno | 2 | 2 | 50 | 50 | 0 | 1 | override_rate(2): 100,50; consiglio_accuracy(2): 0,50; last_prediction_valid(2): "",false; last_prediction_reason(2): "azione_chiusura_senza_previsi,"finestra_c | prediction_checked 1, close_concordante 1 | 5 | 16.67 |
| sala | 2 | 2 | 50 | 50 | 0 | 1 | override_rate(2): 100,50; consiglio_accuracy(2): 0,50; last_prediction_valid(2): "",false; last_prediction_reason(2): "azione_chiusura_senza_previsi,"finestra_c | prediction_checked 1, close_concordante 1 | 8 | 75 |

_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._

## 7. Efficacia delle aperture (osservata)

did = variazione di omega della stanza meno quella delle altre stanze con finestra chiusa (stesso intervallo). `eff_regola_RH` applica la regola attuale (RH scende >= 2 punti in 60 min), `eff_fisica` richiede did60 < -0.3 g/kg.


| gruppo | n | dur_med | con_impianto | dRH60_med | dOmega60_med | did60_med | n_did | eff_regola_RH_pct | eff_fisica_pct |
|---|---|---|---|---|---|---|---|---|---|
| tutte | 5 | 6.62 | 5 | - | - | - | 0 | - | - |
| dopo consiglio apri | 0 | - | 0 | - | - | - | 0 | - | - |
| senza consiglio | 5 | 6.62 | 5 | - | - | - | 0 | - | - |
| durata < 1 min | 1 | 0.72 | 1 | - | - | - | 0 | - | - |
| durata >= 5 min | 4 | 8.31 | 4 | - | - | - | 0 | - | - |
| durata >= 5 min e consiglio | 0 | - | 0 | - | - | - | 0 | - | - |
| durata >= 5 min senza consiglio | 4 | 8.31 | 4 | - | - | - | 0 | - | - |


**Previsione umidita' vs reale all'orizzonte** (n=5): errore mediano 3.60 punti RH, MAE 4.42, correlazione -0.06


**Ultime 30 aperture** (dRH in punti %, dOmega in g/kg):


| stanza | inizio | dur_min | fine | consiglio_apri_prima | impianto | t_ext | dw0 | dRH30 | dRH60 | dOmega30 | dOmega60 | did60 | n_ctrl60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | 10-31 11:33 | 10 | fine_dati | False | True | 17.80 | 0.97 | - | - | - | - | - | 0 |
| camera_grande | 10-31 11:33 | 6.16 | off | False | True | 17.80 | 0.05 | - | - | - | - | - | 0 |
| camera | 10-31 11:33 | 10 | fine_dati | False | True | 17.80 | 0.83 | - | - | - | - | - | 0 |
| bagno | 10-31 11:33 | 0.72 | off | False | True | 17.80 | 0.41 | - | - | - | - | - | 0 |
| sala | 10-31 11:33 | 6.62 | off | False | True | 17.80 | 0.12 | - | - | - | - | - | 0 |


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
| cucina | 2 | 2.50 | 2.95 | 0 | 2 | 0.15 | 0.15 |
| camera_grande | 2 | 5 | 5 | 0 | 2 | 0.13 | 0.13 |
| camera | 2 | 21.50 | 21.95 | 100 | 2 | 0.13 | 0.14 |
| corridoio | - | - | - | - | 2 | 0.12 | 0.12 |
| bagno | - | - | - | - | 2 | 0.14 | 0.14 |
| sala | - | - | - | - | 2 | 0.13 | 0.13 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=17.8, p10=18.1, p50=18.8, p90=19.4, max=19.5; RH_ext min=40, p10=41, p50=43, p90=45, max=46; omega_ext min=5.88, p10=5.91, p50=6.09, p90=6.22, max=6.29; fonti: clima_locale 47


**Pioggia:** 0.0% dei campioni > 0 (n=1).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 47 | 0 | 19.50 | 6.29 | 46 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

_nessun dato_

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 6 | 0 | 0 | 1 | 0 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 8926; entita' del sistema clima (nome contiene stanza e sensore tipo): 1201 (13.5%)

| entita | righe |
|---|---|
| sensor.potenza_carichi_non_misurati | 473 |
| sensor.consumo_casa_rapido | 447 |
| sensor.net_grid_power | 383 |
| sensor.prism_tensione_attuale | 289 |
| sensor.locale_tecnico_prism_power_grid_voltage | 289 |
| sensor.consumo_impianto_nuovo | 245 |
| sensor.prism_potenza | 202 |
| sensor.prism_potenza_kw | 202 |
| sensor.locale_tecnico_prism_power_provided_to_car | 202 |
| sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_potenza | 131 |
| sensor.potenza_totale_bilancio | 130 |
| sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_voltaggio | 126 |
| sensor.lavastoviglie_wifi_digital_meter_lavastoviglie_corrente | 111 |
| sensor.cucina_calibrazione_riepilogo | 84 |
| sensor.ev_charging_status_markdown | 75 |
| automation.log_ev_charging_reason_changes | 74 |
| sensor.potenza_consumo_casa_reale | 73 |
| sensor.potenza_totale_entrante | 72 |
| sensor.potenza_differenza_contatori | 69 |
| sensor.corridoio_calibrazione_riepilogo | 66 |
