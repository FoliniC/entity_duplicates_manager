# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 07:03 a 2026-10-29 09:03 (Europe/Rome); righe lette: 8865; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
- sala: analytics_tuning praticamente fermo (prediction_count=0, fattori=1.0)


## 1. Entita' attese (esistenza e righe nel periodo)

- Attese: 117; assenti nel recorder: 7; presenti ma senza righe nel periodo: 0

**Assenti (mai registrate):** sensor.esito_ultimo_consiglio_finestra_bagno, sensor.esito_ultimo_consiglio_finestra_camera, sensor.esito_ultimo_consiglio_finestra_camera_grande, sensor.esito_ultimo_consiglio_finestra_corridoio, sensor.esito_ultimo_consiglio_finestra_corridoio_con_validazione, sensor.esito_ultimo_consiglio_finestra_cucina, sensor.esito_ultimo_consiglio_finestra_sala


**Entita' 'esito' / 'fancoil_events' presenti nel recorder:** automation.bagno_notifica_esito_consiglio_finestra, automation.camera_grande_notifica_esito_consiglio_finestra, automation.camera_notifica_esito_consiglio_finestra, automation.corridoio_notifica_esito_consiglio_finestra, automation.cucina_notifica_esito_consiglio_finestra, automation.reset_sessione_esito_bloccata_bagno, automation.reset_sessione_esito_bloccata_camera, automation.reset_sessione_esito_bloccata_camera_grande, automation.reset_sessione_esito_bloccata_cucina, automation.reset_sessione_esito_bloccata_sala, automation.sala_notifica_esito_consiglio_finestra, sensor.esito_ultimo_consiglio_finestra_bagno_con_validazione, sensor.esito_ultimo_consiglio_finestra_bagno_validated, sensor.esito_ultimo_consiglio_finestra_bagno_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_con_validazione, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated, sensor.esito_ultimo_consiglio_finestra_camera_grande_validated_v3, sensor.esito_ultimo_consiglio_finestra_camera_validated, sensor.esito_ultimo_consiglio_finestra_camera_validated_v3, sensor.esito_ultimo_consiglio_finestra_cucina_con_validazione, sensor.esito_ultimo_consiglio_finestra_cucina_validated, sensor.esito_ultimo_consiglio_finestra_cucina_validated_v3, sensor.esito_ultimo_consiglio_finestra_sala_con_validazione, sensor.esito_ultimo_consiglio_finestra_sala_validated, sensor.esito_ultimo_consiglio_finestra_sala_validated_v3


**Candidati contatto/finestra trovati nel recorder** (quota di tempo):

| entita | righe | on | off | unavailable |
|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 4 | 0.08 | 0.92 | 0.00 |
| binary_sensor.contact_cucina_not_used | 4 | 0.08 | 0.92 | 0.00 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 4 | 0.08 | 0.91 | 0.00 |
| binary_sensor.finestra_camera_grande_not_used | 4 | 0.08 | 0.91 | 0.00 |
| binary_sensor.finestracucina_alert | 2 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 3 | 1.00 | 0 | 0.00 |
| binary_sensor.finestracucina_motion | 2 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 3 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 1 | 0 | 1 | 0 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 1 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 1 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 1 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 1 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 3 | 0 | 1.00 | 0.00 |
| input_boolean.finestra_bagno_aperta | 3 | 0.06 | 0.94 | 0 |
| input_boolean.finestra_camera_aperta | 1 | 0 | 1 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 1 | 0 | 1 | 0 |
| input_boolean.finestra_cucina_aperta | 1 | 0 | 1 | 0 |
| input_boolean.finestra_sala_aperta | 1 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 16 | 0 | 61.27 | 45.15 | 51.50 | 58.85 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 16 | 0.13 | 61.27 | 45.14 | 51 | 58.86 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 4 | 0 | 924.49 | 50.03 | 52.50 | 54 | 0 | 0 | 0 | False | 3 |
| cucina | t_reale | 16 | 0 | 54.41 | 18.83 | 19.40 | 20 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 16 | 0.13 | 54.41 | 18.83 | 19.40 | 20 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 58 | 0 | 0.31 | 6.44 | 7.38 | 9.06 | 0 | 0 | 0 | False | 0.14 |
| camera_grande | rh_pilota | 18 | 0 | 60.41 | 45.17 | 52 | 61.66 | 0 | 0 | 0 | False | 2 |
| camera_grande | rh_fancoil | 18 | 0.12 | 60.41 | 45.16 | 52 | 61.68 | 0 | 0 | 0 | False | 2 |
| camera_grande | rh_th | 4 | 0 | 732.89 | 50 | 52 | 54 | 0 | 0 | 0 | False | 4 |
| camera_grande | t_reale | 99 | 0 | 5.11 | 17.80 | 19.20 | 19.80 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 99 | 0.12 | 5.11 | 17.79 | 19.20 | 19.81 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 115 | 0 | 5.79 | 6.08 | 7.87 | 9.18 | 0 | 0 | 0 | False | 0.10 |
| camera | rh_pilota | 2 | 0 | 1549.83 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 3 | 0.12 | 777.90 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_th | 2 | 0 | 1550.19 | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 5 | 0 | 777.12 | 20 | 20.20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 6 | 0.12 | 8.37 | 20 | 20.20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 8 | 0 | 24.91 | 8.43 | 8.54 | 8.55 | 0 | 0 | 0 | False | 0.01 |
| corridoio | rh_pilota | 17 | 0 | 61.66 | 42.16 | 48 | 55.84 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 17 | 0.13 | 61.66 | 42.15 | 47.50 | 55.85 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 27 | 0 | 4.42 | 20.40 | 20.60 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 27 | 0.13 | 4.42 | 20.40 | 20.60 | 21.15 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 82 | 0 | 1.78 | 6.59 | 7.47 | 9.26 | 0 | 0 | 0 | False | 0.10 |
| bagno | rh_pilota | 20 | 0 | 60.24 | 43.19 | 51.50 | 59.81 | 0 | 0 | 0 | False | 2 |
| bagno | rh_fancoil | 20 | 0.13 | 60.24 | 43.18 | 51 | 59.82 | 0 | 0 | 0 | False | 1.50 |
| bagno | t_reale | 46 | 0 | 18.58 | 17.29 | 19.30 | 20 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 48 | 0.13 | 16.79 | 17.29 | 19.20 | 19.91 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 65 | 0 | 18.69 | 5.77 | 7.58 | 9.12 | 0 | 0 | 0 | False | 0.09 |
| sala | rh_pilota | 7 | 0 | 635.03 | 54.06 | 55 | 56 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 7 | 0.12 | 643.07 | 54.05 | 55 | 56 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 32 | 0 | 7.40 | 20.20 | 20.40 | 20.40 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 35 | 0.12 | 7.41 | 20.20 | 20.40 | 20.40 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 72 | 0 | 2.82 | 8.53 | 8.65 | 8.81 | 0 | 0 | 0 | False | 0.11 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 1 | 9.33 | 9.33 | 7.77 | 0.11 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 1 | 9.49 | 9.49 | 7.91 | 0.10 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 1 | 6.84 | 6.84 | 5.70 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0.30 | 0 | 0 | 775.06 | nessuna_azione 77%, apri 13%, chiudi 9% |
| camera_grande | 0.30 | 0 | 0 | 775.06 | nessuna_azione 77%, apri 12%, chiudi 11% |
| camera | 0 | 0 | 0 | 7200.46 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 7200.19 | nessuna_azione 100% |
| bagno | 0.30 | 0 | 0 | 775.07 | nessuna_azione 77%, apri 13%, chiudi 9% |
| sala | 0 | 0 | 0 | 7200.37 | nessuna_azione 100% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0.30 | 0.30 | 0.30 | 0.20 | 0.20 |
| camera_grande | 0.30 | 0.30 | 0.30 | 0.20 | 0.20 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0.30 | 0.30 | 0.30 | 0.20 | 0.20 |
| sala | 0 | 0 | 0 | 0 | 0 |


**Soglie effettive quando consiglia 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):

| stanza | impianto | ore_apri | dw_min_grezzo | dw_min_stabile30s | dw_p10_t | dw_p50_t | calo_min_stab | calo_p50_t |
|---|---|---|---|---|---|---|---|---|
| cucina | False | 0.27 | 0.02 | 0.02 | 0.07 | 1.80 | 0 | 3.10 |
| camera_grande | False | 0.24 | -0.81 | -0.81 | -0.76 | 4.36 | -1.40 | 7.60 |
| bagno | False | 0.27 | -0.62 | -0.62 | -0.59 | 1.80 | -1.10 | 3.10 |

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
| cucina | 2 | 1 | 0 | 0 | 0 | 1.0 | - | idle 2 | 8 | 99.79 |
| camera_grande | 2 | 1 | 0 | 0 | 0 | 1.0 | - | idle 2 | 8 | 99.85 |
| camera | 2 | 1 | 0 | 0 | 0 | 1.0 | - | idle 2 | 8 | 99.77 |
| corridoio | 2 | 1 | 0 | 0 | 0 | 1.0 | - | idle 2 | 8 | 99.81 |
| bagno | 5 | 4 | 0 | 0 | 0 | 1.0 | override_rate(2): "0",0; consiglio_accuracy(2): "0",100; prediction_factor_humidity(2): "1.0",1.0; prediction_factor_temperature(2): "1.0",1.0; prediction_facto | idle 2, open_concordante 1, prediction_checked 1, close_concordante 1 | 8 | 99.82 |
| sala | 2 | 1 | 0 | 0 | 0 | 1.0 | - | idle 2 | 8 | 99.80 |

_attributi_variabili = attributi di analytics_tuning che assumono piu' valori nel periodo (n valori distinti: esempi)._

## 7. Efficacia delle aperture (osservata)

did = variazione di omega della stanza meno quella delle altre stanze con finestra chiusa (stesso intervallo). `eff_regola_RH` applica la regola attuale (RH scende >= 2 punti in 60 min), `eff_fisica` richiede did60 < -0.3 g/kg.


| gruppo | n | dur_med | con_impianto | dRH60_med | dOmega60_med | did60_med | n_did | eff_regola_RH_pct | eff_fisica_pct |
|---|---|---|---|---|---|---|---|---|---|
| tutte | 3 | 9.33 | 0 | -8 | -1.53 | -1.09 | 3 | 66.67 | 66.67 |
| dopo consiglio apri | 3 | 9.33 | 0 | -8 | -1.53 | -1.09 | 3 | 66.67 | 66.67 |
| senza consiglio | 0 | - | 0 | - | - | - | 0 | - | - |
| durata < 1 min | 0 | - | 0 | - | - | - | 0 | - | - |
| durata >= 5 min | 3 | 9.33 | 0 | -8 | -1.53 | -1.09 | 3 | 66.67 | 66.67 |
| durata >= 5 min e consiglio | 3 | 9.33 | 0 | -8 | -1.53 | -1.09 | 3 | 66.67 | 66.67 |
| durata >= 5 min senza consiglio | 0 | - | 0 | - | - | - | 0 | - | - |


**Accordo regola-RH vs fisica (righe: regola, colonne: fisica):**

```
fis_eff  False  True 
sys_eff              
False        1      0
True         0      2
```


**Previsione umidita' vs reale all'orizzonte** (n=3): errore mediano -7.30 punti RH, MAE 6.53, correlazione 1.00


**Ultime 30 aperture** (dRH in punti %, dOmega in g/kg):


| stanza | inizio | dur_min | fine | consiglio_apri_prima | impianto | t_ext | dw0 | dRH30 | dRH60 | dOmega30 | dOmega60 | did60 | n_ctrl60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bagno | 10-29 07:12 | 6.84 | off | True | False | 10.90 | 0.51 | -1 | 0 | -0.45 | -0.20 | -0.13 | 3 |
| cucina | 10-29 07:10 | 9.33 | off | True | False | 9.20 | 1.80 | -10 | -8 | -1.83 | -1.53 | -1.09 | 3 |
| camera_grande | 10-29 07:09 | 9.49 | off | True | False | 9.20 | 4.36 | -10 | -9 | -2.14 | -1.80 | -1.30 | 3 |


## 8. Consigli 'apri' (episodi >= 60 s) seguiti da un'apertura entro 15 min

| stanza | episodi_apri_tot | episodi_ge60s | durata_med_min | seguiti | seguiti_pct | tempo_in_apri_pct |
|---|---|---|---|---|---|---|
| cucina | 2 | 2 | 8.09 | 1 | 50 | 13.48 |
| camera_grande | 2 | 2 | 7.09 | 1 | 50 | 11.81 |
| camera | 0 | 0 | - | 0 | - | 0 |
| bagno | 2 | 2 | 8.09 | 1 | 50 | 13.48 |
| sala | 0 | 0 | - | 0 | - | 0 |

_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._

## 9. Coerenza tra sensori

| stanza | pilota_vs_th_n | pilota_vs_th_p50 | pilota_vs_th_p95 | oltre15_pct | omega_n | omega_bias_med | omega_abs_p95 |
|---|---|---|---|---|---|---|---|
| cucina | 24 | 3 | 6 | 0 | 24 | 0.17 | 0.20 |
| camera_grande | 24 | 3 | 7.55 | 0 | 24 | 0.17 | 0.18 |
| camera | 24 | 9 | 9 | 0 | 24 | 0.19 | 0.20 |
| corridoio | - | - | - | - | 24 | 0.17 | 0.20 |
| bagno | - | - | - | - | 24 | 0.17 | 0.20 |
| sala | - | - | - | - | 24 | 0.19 | 0.19 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=9.2, p10=9.6, p50=10.4, p90=14.5, max=16.6; RH_ext min=52, p10=55, p50=67, p90=85, max=99; omega_ext min=5.09, p10=5.25, p50=5.74, p90=7.47, max=8.36; fonti: clima_locale 477


**Pioggia:** 0.0% dei campioni > 0 (n=2).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 477 | 0 | 16.60 | 8.36 | 99 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 1 | 1 | 0.13 | 0.13 | 10-29 07:28 | 0 | 7h:1 |
| sensor.fancoil_cucina_humidity | 1 | 1 | 0.16 | 0.16 | 10-29 07:28 | 0 | 7h:1 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 1 | 1 | 0.12 | 0.12 | 10-29 07:28 | 0 | 7h:1 |
| sensor.fancoil_camera_grande_humidity | 1 | 1 | 0.15 | 0.15 | 10-29 07:28 | 0 | 7h:1 |
| sensor.fancoil_camera_humidity | 1 | 1 | 0.14 | 0.14 | 10-29 07:28 | 0 | 7h:1 |
| sensor.fancoil_corridoio_humidity | 1 | 1 | 0.15 | 0.15 | 10-29 07:28 | 0 | 7h:1 |
| sensor.fancoil_bagno_humidity | 1 | 1 | 0.16 | 0.16 | 10-29 07:28 | 0 | 7h:1 |
| sensor.fancoil_sala_humidity | 1 | 1 | 0.15 | 0.15 | 10-29 07:28 | 0 | 7h:1 |
| binary_sensor.contact_cucina_not_used | 1 | 1 | 0.13 | 0.13 | 10-29 07:28 | 0 | 7h:1 |
| binary_sensor.finestra_camera_grande_not_used | 1 | 1 | 0.12 | 0.12 | 10-29 07:28 | 0 | 7h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 9 | 9 | 9 | 1 | 1 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 10 | 10 | 10 | 1 | 1 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 55637; entita' del sistema clima (nome contiene stanza e sensore tipo): 16468 (29.6%)

| entita | righe |
|---|---|
| sensor.statistics_temperatura_sala_variance | 1346 |
| sensor.statistics_temperatura_camera_grande_variance | 1344 |
| sensor.statistics_temperatura_camera_variance | 1342 |
| sensor.statistics_temperatura_bagno_variance | 1341 |
| sensor.previsione_finestra_camera_grande | 1310 |
| sensor.consumo_impianto_nuovo | 1162 |
| sensor.previsione_finestra_bagno | 1097 |
| sensor.previsione_finestra_corridoio | 1027 |
| sensor.previsione_finestra_sala | 997 |
| sensor.previsione_finestra_cucina | 940 |
| sensor.previsione_finestra_camera | 873 |
| automation.fancoil_listener_eventi_log | 801 |
| automation.ev_listener_eventi_log | 685 |
| sensor.knx_interface_telegrams | 682 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 630 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 629 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 624 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 621 |
| sensor.smart_meter_2026_a_pdc_total_power | 601 |
| sensor.smart_meter_2026_a_pdc_voltage_a | 599 |
