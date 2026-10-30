# Report diagnostico clima (v1.3)

Periodo: da 2026-10-29 06:43 a 2026-10-29 10:43 (Europe/Rome); righe lette: 17861; stanze: cucina, camera_grande, camera, corridoio, bagno, sala

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
| binary_sensor.contact_cucina_contact_cucina | 16 | 0.04 | 0.95 | 0.01 |
| binary_sensor.contact_cucina_not_used | 16 | 0.04 | 0.95 | 0.01 |
| binary_sensor.contact_sensor_doorcontact_state | 0 | 0 | 0 | - |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 16 | 0.04 | 0.95 | 0.01 |
| binary_sensor.finestra_camera_grande_not_used | 16 | 0.04 | 0.95 | 0.01 |
| binary_sensor.finestracucina_alert | 14 | 0 | 0 | 1 |
| binary_sensor.finestracucina_connected | 21 | 1.00 | 0 | 0.00 |
| binary_sensor.finestracucina_motion | 14 | 0 | 0 | 1 |
| binary_sensor.finestracucina_recording | 21 | 0 | 1.00 | 0.00 |
| binary_sensor.garage_door_contact_filtered | 7 | 0 | 1.00 | 0 |
| binary_sensor.garage_door_garage_contact_sensor | 0 | 0 | 0 | - |
| binary_sensor.piazzale_mg_mg4_electric_window_front_left | 7 | 0 | 1.00 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_front_right | 7 | 0 | 1 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_left | 7 | 0 | 1.00 | 0 |
| binary_sensor.piazzale_mg_mg4_electric_window_rear_right | 7 | 0 | 1 | 0 |
| binary_sensor.wifi_garage_door_module_garage_contact | 21 | 0 | 0.99 | 0.01 |
| input_boolean.finestra_bagno_aperta | 9 | 0.03 | 0.97 | 0 |
| input_boolean.finestra_camera_aperta | 7 | 0 | 1 | 0 |
| input_boolean.finestra_camera_grande_aperta | 0 | 0 | 0 | - |
| input_boolean.finestra_corridoio_aperta | 7 | 0 | 1.00 | 0 |
| input_boolean.finestra_cucina_aperta | 7 | 0 | 1 | 0 |
| input_boolean.finestra_sala_aperta | 7 | 0 | 1 | 0 |

## 2. Qualita' dei sensori

| stanza | sensore | righe | unavail_pct | upd_med_s | p1 | p50 | p99 | fuori_range | fuori_pct | zeri | costante | step_p50 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cucina | rh_pilota | 23 | 0 | 505.81 | 45.22 | 54 | 58.78 | 0 | 0 | 0 | False | 1 |
| cucina | rh_fancoil | 29 | 0.46 | 91.37 | 45.21 | 53.50 | 58.79 | 0 | 0 | 0 | False | 1 |
| cucina | rh_th | 11 | 0 | 1020.54 | 50.10 | 51 | 54 | 0 | 0 | 0 | False | 3 |
| cucina | t_reale | 143 | 0 | 6.95 | 19.08 | 19.60 | 20 | 0 | 0 | 0 | False | 0.20 |
| cucina | t_fancoil | 149 | 0.46 | 7.00 | 19.08 | 19.60 | 19.92 | 0 | 0 | 0 | False | 0.20 |
| cucina | omega | 308 | 0 | 1.74 | 6.61 | 7.92 | 8.89 | 0 | 0 | 0 | False | 0.10 |
| camera_grande | rh_pilota | 25 | 0 | 250.91 | 45.24 | 54 | 61.52 | 0 | 0 | 0 | False | 2 |
| camera_grande | rh_fancoil | 31 | 0.44 | 60.59 | 45.23 | 54.50 | 61.54 | 0 | 0 | 0 | False | 2 |
| camera_grande | rh_th | 12 | 0 | 573.99 | 50 | 50 | 54 | 0 | 0 | 0 | False | 2.50 |
| camera_grande | t_reale | 203 | 0 | 5.11 | 18 | 19.20 | 19.60 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | t_fancoil | 209 | 0.44 | 5.12 | 18 | 19.20 | 19.60 | 0 | 0 | 0 | False | 0.20 |
| camera_grande | omega | 220 | 0 | 5.17 | 6.16 | 8.02 | 8.89 | 0 | 0 | 0 | False | 0.10 |
| camera | rh_pilota | 8 | 0 | 598.43 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_fancoil | 15 | 0.40 | 165.08 | 55 | 55 | 55 | 0 | 0 | 0 | False | - |
| camera | rh_th | 8 | 0 | 598.25 | 64 | 64 | 64 | 0 | 0 | 0 | False | - |
| camera | t_reale | 47 | 0 | 10.21 | 20 | 20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | t_fancoil | 54 | 0.40 | 9.69 | 20 | 20 | 20.20 | 0 | 0 | 0 | False | 0.20 |
| camera | omega | 50 | 0 | 10.72 | 8.43 | 8.43 | 8.55 | 0 | 0 | 0 | False | 0.11 |
| corridoio | rh_pilota | 27 | 0.05 | 206.92 | 42.25 | 51 | 55.75 | 0 | 0 | 0 | False | 1 |
| corridoio | rh_fancoil | 33 | 0.49 | 80.50 | 42.24 | 51 | 55.76 | 0 | 0 | 0 | False | 1 |
| corridoio | t_reale | 98 | 0 | 8.08 | 20.39 | 20.60 | 21.20 | 0 | 0 | 0 | False | 0.20 |
| corridoio | t_fancoil | 106 | 0.49 | 6.81 | 20.40 | 20.60 | 21.01 | 0 | 0 | 0 | False | 0.20 |
| corridoio | omega | 227 | 0.05 | 2.03 | 6.61 | 8.11 | 9.22 | 0 | 0 | 0 | False | 0.11 |
| bagno | rh_pilota | 27 | 0 | 121.79 | 43.26 | 54 | 59.74 | 0 | 0 | 0 | False | 1.50 |
| bagno | rh_fancoil | 33 | 0.43 | 60.50 | 43.25 | 53.50 | 59.75 | 0 | 0 | 0 | False | 1 |
| bagno | t_reale | 52 | 0 | 24.89 | 17.30 | 19.40 | 20 | 0 | 0 | 0 | False | 0.20 |
| bagno | t_fancoil | 60 | 0.43 | 16.79 | 17.30 | 19.40 | 19.90 | 0 | 0 | 0 | False | 0.20 |
| bagno | omega | 72 | 0 | 22.82 | 5.78 | 7.68 | 9.11 | 0 | 0 | 0 | False | 0.09 |
| sala | rh_pilota | 15 | 0 | 586.29 | 54 | 55 | 56 | 0 | 0 | 0 | False | 1 |
| sala | rh_fancoil | 21 | 0.46 | 475.92 | 54 | 54.50 | 56 | 0 | 0 | 0 | False | 1 |
| sala | t_reale | 70 | 0 | 9.56 | 20.20 | 20.80 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| sala | t_fancoil | 76 | 0.46 | 8.87 | 20.20 | 20.60 | 21.60 | 0 | 0 | 0 | False | 0.20 |
| sala | omega | 146 | 0 | 2.82 | 8.54 | 8.81 | 9.14 | 0 | 0 | 0 | False | 0.11 |

_fuori_range: T 10-35 C, RH 10-95%, omega 1-20 g/kg; costante = un solo valore per tutto il periodo; p1/p99 = percentili._

## 3. Finestre: fonte, aperture, tempo non disponibile

| stanza | fonte | aperture | durata_med_min | durata_p90_min | tempo_aperta_pct | unavail_pct |
|---|---|---|---|---|---|---|
| cucina | binary_sensor.contact_cucina_contact_cucina | 1 | 9.33 | 9.33 | 3.89 | 0.63 |
| camera_grande | binary_sensor.finestra_camera_grande_finestra_camera_grande | 1 | 9.49 | 9.49 | 3.95 | 0.54 |
| camera | input_boolean.finestra_camera_aperta | 0 | - | - | 0 | 0 |
| corridoio | (nessuna finestra) | 0 | - | - | - | - |
| bagno | input_boolean.finestra_bagno_aperta | 1 | 6.84 | 6.84 | 2.85 | 0 |
| sala | input_boolean.finestra_sala_aperta | 0 | - | - | 0 | 0 |

## 4. Consiglio finestra (albero decisionale)

| stanza | cambi_al_giorno | episodi_lt60s_pct | rientri_ABA_lt60s | dwell_med_s | stati_tempo |
|---|---|---|---|---|---|
| cucina | 0.40 | 0 | 0 | 649.84 | nessuna_azione 81%, apri 15%, chiudi 5% |
| camera_grande | 0.30 | 0 | 0 | 1375.06 | nessuna_azione 80%, apri 14%, chiudi 5% |
| camera | 0 | 0 | 0 | 14400.15 | nessuna_azione 100% |
| corridoio | 0 | 0 | 0 | 14400.32 | nessuna_azione 100% |
| bagno | 0.30 | 0 | 0 | 1375.07 | nessuna_azione 80%, apri 15%, chiudi 5% |
| sala | 0 | 0 | 0 | 14400.12 | nessuna_azione 100% |


**Cambi al giorno se si ignorano gli stati piu' brevi di N secondi** (debounce):

| stanza | grezzi | min30s | min60s | min120s | min300s |
|---|---|---|---|---|---|
| cucina | 0.40 | 0.40 | 0.40 | 0.20 | 0.20 |
| camera_grande | 0.30 | 0.30 | 0.30 | 0.20 | 0.20 |
| camera | 0 | 0 | 0 | 0 | 0 |
| corridoio | 0 | 0 | 0 | 0 | 0 |
| bagno | 0.30 | 0.30 | 0.30 | 0.20 | 0.20 |
| sala | 0 | 0 | 0 | 0 | 0 |


**Soglie effettive quando consiglia 'apri/apri_se_riparata'** (pesate sul tempo; 'stabile' = righe che durano >= 30 s):

| stanza | impianto | ore_apri | dw_min_grezzo | dw_min_stabile30s | dw_p10_t | dw_p50_t | calo_min_stab | calo_p50_t |
|---|---|---|---|---|---|---|---|---|
| cucina | False | 0.59 | 0.02 | 0.02 | 0.30 | 3.89 | 0 | 6.70 |
| camera_grande | False | 0.57 | -0.81 | -0.81 | -0.72 | 4.36 | -1.40 | 7.60 |
| bagno | False | 0.60 | -0.62 | -0.62 | -0.07 | 3.89 | -1.10 | 6.70 |

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
| cucina | 8 | 1 | 0 | 0 | 0 | 1.0 | - | idle 8 | 8 | 99.34 |
| camera_grande | 8 | 1 | 0 | 0 | 0 | 1.0 | - | idle 8 | 8 | 99.41 |
| camera | 8 | 1 | 0 | 0 | 0 | 1.0 | - | idle 8 | 8 | 99.17 |
| corridoio | 8 | 1 | 0 | 0 | 0 | 1.0 | - | idle 8 | 8 | 99.01 |
| bagno | 11 | 4 | 0 | 0 | 0 | 1.0 | override_rate(2): "0",0; consiglio_accuracy(2): "0",100; prediction_factor_humidity(2): "1.0",1.0; prediction_factor_temperature(2): "1.0",1.0; prediction_facto | idle 8, open_concordante 1, prediction_checked 1, close_concordante 1 | 8 | 99.22 |
| sala | 8 | 1 | 0 | 0 | 0 | 1.0 | - | idle 8 | 8 | 99.22 |

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
| cucina | 2 | 2 | 17.58 | 1 | 50 | 14.65 |
| camera_grande | 2 | 2 | 17.09 | 1 | 50 | 14.24 |
| camera | 0 | 0 | - | 0 | - | 0 |
| bagno | 2 | 2 | 18.09 | 1 | 50 | 15.07 |
| sala | 0 | 0 | - | 0 | - | 0 |

_Confronta seguiti_pct con tempo_in_apri_pct: se sono simili, l'apertura non e' correlata al consiglio. Nelle stanze con finestra manuale una mancata registrazione appare come consiglio ignorato._

## 9. Coerenza tra sensori

| stanza | pilota_vs_th_n | pilota_vs_th_p50 | pilota_vs_th_p95 | oltre15_pct | omega_n | omega_bias_med | omega_abs_p95 |
|---|---|---|---|---|---|---|---|
| cucina | 48 | 3 | 5.65 | 0 | 48 | 0.17 | 0.20 |
| camera_grande | 48 | 5 | 8 | 0 | 48 | 0.17 | 0.21 |
| camera | 48 | 9 | 9 | 0 | 48 | 0.19 | 0.20 |
| corridoio | - | - | - | - | 48 | 0.17 | 0.20 |
| bagno | - | - | - | - | 48 | 0.17 | 0.20 |
| sala | - | - | - | - | 48 | 0.19 | 0.19 |


_omega_bias = omega del sensore meno omega ricalcolata (Magnus, 980 hPa) da T_reale e RH_pilota, in g/kg._


**Esterno (sensor.omega_esterno):** T_ext min=9.0, p10=9.7, p50=14.0, p90=18.8, max=20.0; RH_ext min=41, p10=45, p50=58, p90=73, max=99; omega_ext min=5.09, p10=5.26, p50=6.26, p90=6.79, max=8.36; fonti: clima_locale 845


**Pioggia:** 0.0% dei campioni > 0 (n=8).


## 9a. Dati esterni: valori impossibili per fonte

| source | righe | anomale | t_max | omega_max | h_max |
|---|---|---|---|---|---|
| clima_locale | 845 | 0 | 20 | 8.36 | 99 |


## 9b. Episodi di indisponibilita' (unavailable/unknown)

| entita | episodi | lt30s | med_min | max_min | max_inizio | min_in_episodi_gt10min | ore_inizio_top |
|---|---|---|---|---|---|---|---|
| binary_sensor.contact_cucina_contact_cucina | 7 | 7 | 0.25 | 0.43 | 10-29 10:02 | 0 | 10h:4, 9h:2, 7h:1 |
| sensor.fancoil_cucina_humidity | 7 | 7 | 0.16 | 0.21 | 10-29 09:52 | 0 | 10h:4, 9h:2, 7h:1 |
| binary_sensor.finestra_camera_grande_finestra_camera_grande | 7 | 7 | 0.19 | 0.36 | 10-29 10:02 | 0 | 10h:4, 9h:2, 7h:1 |
| sensor.fancoil_camera_grande_humidity | 7 | 7 | 0.15 | 0.20 | 10-29 10:02 | 0 | 10h:4, 9h:2, 7h:1 |
| sensor.fancoil_camera_humidity | 7 | 7 | 0.14 | 0.19 | 10-29 09:52 | 0 | 10h:4, 9h:2, 7h:1 |
| sensor.fancoil_corridoio_humidity | 8 | 8 | 0.14 | 0.20 | 10-29 10:41 | 0 | 10h:4, 9h:3, 7h:1 |
| sensor.umidita_corridoio_pilota | 1 | 1 | 0.12 | 0.12 | 10-29 09:48 | 0 | 9h:1 |
| sensor.fancoil_bagno_humidity | 7 | 7 | 0.16 | 0.19 | 10-29 10:02 | 0 | 10h:4, 9h:2, 7h:1 |
| sensor.fancoil_sala_humidity | 7 | 7 | 0.15 | 0.20 | 10-29 09:52 | 0 | 10h:4, 9h:2, 7h:1 |
| binary_sensor.contact_cucina_not_used | 7 | 7 | 0.25 | 0.43 | 10-29 10:02 | 0 | 10h:4, 9h:2, 7h:1 |
| binary_sensor.finestra_camera_grande_not_used | 7 | 7 | 0.19 | 0.36 | 10-29 10:02 | 0 | 10h:4, 9h:2, 7h:1 |

## 9c. Contatto principale vs secondo ingresso ('not_used')

| principale | secondaria | on_min_princ | on_min_sec | sovrapposti_min | eventi_on_princ | eventi_on_sec |
|---|---|---|---|---|---|---|
| contact_cucina_contact_cucina | contact_cucina_not_used | 9 | 9 | 9 | 1 | 1 |
| finestra_camera_grande_finestra_ | finestra_camera_grande_not_used | 10 | 10 | 10 | 1 | 1 |

_Se i minuti sovrapposti sono pochi e la secondaria ha eventi propri, il secondo ingresso e' cablato a un'altra apertura._

## 10. Impronta sul recorder

- Righe totali nel periodo: 127945; entita' del sistema clima (nome contiene stanza e sensore tipo): 32964 (25.8%)

| entita | righe |
|---|---|
| automation.fancoil_listener_eventi_log | 3117 |
| sensor.statistics_temperatura_camera_variance | 2631 |
| sensor.statistics_temperatura_sala_variance | 2626 |
| sensor.statistics_temperatura_camera_grande_variance | 2624 |
| sensor.statistics_temperatura_bagno_variance | 2623 |
| sensor.previsione_finestra_camera_grande | 2382 |
| sensor.consumo_impianto_nuovo | 2343 |
| sensor.previsione_finestra_cucina | 2123 |
| sensor.previsione_finestra_corridoio | 1921 |
| sensor.previsione_finestra_bagno | 1802 |
| sensor.previsione_finestra_sala | 1796 |
| sensor.previsione_finestra_camera | 1692 |
| automation.ev_listener_eventi_log | 1411 |
| sensor.knx_interface_telegrams | 1384 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_a | 1282 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_total_power | 1280 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_power_b | 1260 |
| sensor.locale_tecnico_wifi_dual_meter_b_new_a_old_current_a | 1256 |
| sensor.smart_meter_2026_a_pdc_total_power | 1224 |
| sensor.smart_meter_2026_a_pdc_power_a | 1209 |
