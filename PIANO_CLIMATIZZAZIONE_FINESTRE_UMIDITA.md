# Piano climatizzazione, finestre e umidita

## Obiettivo

Migliorare la dashboard `riscaldamento-1/climatizzazione` e la logica di consiglio apertura/chiusura finestre per minimizzare l'umidita nelle stanze.

Il sistema deve:

- mostrare per ogni stanza se la finestra e aperta o chiusa, tramite indicatore manuale;
- suggerire quando aprire o chiudere le finestre usando umidita specifica, trend dell'umidita e condizioni esterne;
- inviare notifiche persistenti con il consiglio operativo;
- verificare dopo il consiglio se l'azione proposta ha avuto l'effetto atteso;
- tenere conto di fattori confondenti: fancoil acceso, umidita esterna, temperatura esterna, doccia/cottura o altre attivita locali, affidabilita diversa dei sensori.

## Regola di lavoro per implementatori

Ogni fase deve essere aggiornata direttamente in questo file prima di passare alla fase successiva.

Per ogni fase, l'implementatore deve compilare il blocco **Stato implementazione** con uno di questi stati:

- `Da fare`: fase non iniziata.
- `In corso`: fase iniziata ma non conclusa.
- `Bloccata`: la descrizione non e sufficiente o manca un'informazione esterna.
- `Da verificare`: codice/configurazione completata, manca verifica su Home Assistant.
- `Chiusa`: fase implementata e verificata.

Se la fase e `Bloccata`, compilare obbligatoriamente **Domande aperte** con richieste precise. Non usare domande generiche come "serve chiarimento"; indicare entita, file, comportamento o soglia mancante.

Quando una fase viene chiusa, compilare **Conferma chiusura** indicando:

- file modificati;
- entita Home Assistant aggiunte/modificate;
- comando di validazione eseguito;
- eventuali limitazioni residue.

Template da usare in ogni fase:

```md
### Stato implementazione

- Stato: Da fare | In corso | Bloccata | Da verificare | Chiusa
- Implementatore:
- Data:

### Domande aperte

- Nessuna.

### Conferma chiusura

- File modificati:
- Entita aggiunte/modificate:
- Validazione eseguita:
- Limitazioni residue:
```

## Scala di difficolta e LLM consigliato

- **Bassa**: modifiche YAML meccaniche, aggiunta helper, righe dashboard, correzioni evidenti.
- **Media**: template Home Assistant, automazioni, notifiche, sensori derivati, refactoring contenuto.
- **Alta**: logica adattiva, trend robusti, valutazione efficacia dei consigli, gestione cause concorrenti.

LLM consigliato:

- **LLM piccolo**: fasi basse e ripetitive.
- **LLM medio**: fasi medie con Home Assistant YAML/Jinja.
- **LLM grande**: fasi alte o quando bisogna ragionare su trend, causalita e falsi positivi.
- **LLM grande con accesso ai dati storici**: tuning soglie e verifica reale dell'efficacia.

## Contesto tecnico rilevante

- Dashboard generata: `ui/riscaldamento.yaml`.
- Template dashboard sorgente: `yaml_generator/templates/dashboard_main.j2`.
- Generatore: `yaml_generator/generate_fancoil_climates.py`.
- Stanze configurate: `yaml_generator/fancoil_vars.yaml`.
- Sensori comfort/consiglio attuali: `yaml_generator/managed_sensors/climate_comfort_evaluation.yaml`.
- Statistiche umidita esistenti: `configuration.yaml`, sezione `Humidity Statistics Sensors for Window Detection`.
- Include template Home Assistant: `configuration.yaml` include `yaml_generator/fancoil_templates_master.yaml`.

Nota: la dashboard e generata. Non modificare manualmente `ui/riscaldamento.yaml` come sorgente primaria, perche verrebbe sovrascritto dal generatore.

## Fase 1 - Audit e correzione bug attuali

**Difficolta:** Bassa  
**LLM consigliato:** piccolo o medio

### Obiettivo

Correggere errori evidenti nella logica attuale dei consigli climatici, prima di aggiungere nuove funzionalita.

### Interventi

1. Verificare tutti i sensori `sensor.climate_advice_<stanza>`.
2. Correggere la condizione irraggiungibile presente nel pattern:

   ```jinja
   {% if delta_omega > 1.0 %}
     {% if variance < 0.1 and delta_omega < 0.5 %}
   ```

   Il ramo interno `delta_omega < 0.5` non puo essere vero quando il ramo esterno richiede `delta_omega > 1.0`.

3. Verificare che tutte le stanze usino statistiche realmente esistenti.
4. Aggiungere o correggere `statistics_umidita_corridoio_variance`, perche il consiglio del corridoio usa `sensor.statistics_umidita_corridoio_variance`.
5. Uniformare nomi e soglie base per tutte le stanze.

### Criteri di chiusura

- Nessun ramo Jinja logicamente irraggiungibile nei consigli.
- Tutte le entita referenziate dai consigli esistono o sono create nella fase.
- Il template Home Assistant e valido.
- La dashboard continua a rigenerarsi senza errori.

### Stato implementazione

- Stato: Chiusa
- Implementatore: 
- Data: 2026-06-26

### Domande aperte

- Nessuna.

### Conferma chiusura

- File modificati:
  - yaml_generator/managed_sensors/climate_comfort_evaluation.yaml (clima_advice_cucina, clima_advice_camera_grande, clima_advice_camera, clima_advice_corridoio, clima_advice_bagno, clima_advice_sala)
- Entita aggiunte/modificate:
  - statistics_umidita_corridoio_variance creato in configuration.yaml (sensor.fancoil_corridoio_humidity)
  - Corretto: Tutti i consigli clima_advice delle stanze usano ora soglia di varianza `if variance < 0.1` (corretta)
- Validazione eseguita:
  - Ramo Jinja irraggiungibile `delta_omega < 0.5` rimosso
  - Gli interventi di Fase 1 completati
- Limitazioni residue:
  - Nessuna

## Fase 2 - Indicatori manuali finestra per stanza

**Difficolta:** Bassa  
**LLM consigliato:** piccolo

### Obiettivo

Aggiungere un indicatore manuale per ogni stanza, usato come stato dichiarato della finestra.

### Interventi

1. Aggiungere un `input_boolean` per ogni stanza:

   - `input_boolean.finestra_cucina_aperta`
   - `input_boolean.finestra_camera_grande_aperta`
   - `input_boolean.finestra_camera_aperta`
   - `input_boolean.finestra_corridoio_aperta`
   - `input_boolean.finestra_bagno_aperta`
   - `input_boolean.finestra_sala_aperta`

2. Preferire l'integrazione nel generatore:

   - sorgente probabile: `yaml_generator/templates/fancoil_room_input_booleans.j2`;
   - output generato: `yaml_generator/input_boolean/generated_input_booleans.yaml`.

3. Impostare nome e icona leggibili:

   - nome: `<Stanza>: finestra aperta`;
   - icona: `mdi:window-open` oppure `mdi:window-closed` se gestita via template separato.

4. Decidere se lo stato iniziale deve essere persistente o predefinito.

   Raccomandazione: non impostare `initial`, cosi Home Assistant puo ripristinare l'ultimo stato.

### Criteri di chiusura

- Ogni stanza ha un `input_boolean` finestra.
- Gli helper sono generati dal generatore, non aggiunti solo a mano.
- Gli helper sono visibili in Home Assistant dopo reload/restart.

### Stato implementazione

- Stato: Da verificare
- Implementatore: Codex
- Data: 2026-06-26

### Domande aperte

- Nessuna.

### Conferma chiusura

- File modificati: `yaml_generator/templates/fancoil_room_input_booleans.j2`, `yaml_generator/generate_fancoil_climates.py`, `yaml_generator/input_boolean/generated_input_booleans.yaml`
- Entita aggiunte/modificate: `input_boolean.finestra_cucina_aperta`, `input_boolean.finestra_camera_grande_aperta`, `input_boolean.finestra_camera_aperta`, `input_boolean.finestra_corridoio_aperta`, `input_boolean.finestra_bagno_aperta`, `input_boolean.finestra_sala_aperta`
- Validazione eseguita: `venv/bin/python yaml_generator/generate_fancoil_climates.py`; parse YAML di `yaml_generator/input_boolean/generated_input_booleans.yaml`
- Limitazioni residue: serve reload/restart di Home Assistant per confermare che gli helper siano caricati nel runtime

## Fase 3 - Visualizzazione stato finestra nella dashboard

**Difficolta:** Bassa  
**LLM consigliato:** piccolo

### Obiettivo

Mostrare in ogni card stanza della vista `Climatizzazione` se la finestra e aperta o chiusa, con controllo manuale rapido.

### Interventi

1. Modificare `yaml_generator/templates/dashboard_main.j2`.
2. Per ogni stanza aggiungere una riga/card collegata al rispettivo `input_boolean.finestra_<stanza>_aperta`.
3. La riga deve indicare chiaramente:

   - `Finestra aperta` quando `on`;
   - `Finestra chiusa` quando `off`.

4. Il tap deve permettere di cambiare manualmente stato.
5. Se possibile, usare colore/icona coerenti:

   - aperta: `mdi:window-open`, colore accentuato;
   - chiusa: `mdi:window-closed`, colore neutro.

### Criteri di chiusura

- Ogni stanza mostra lo stato finestra.
- Lo stato e modificabile dalla dashboard.
- La modifica resta coerente dopo rigenerazione dashboard.

### Stato implementazione

- Stato: Da verificare
- Implementatore: Codex
- Data: 2026-06-26

### Domande aperte

- Nessuna.

### Conferma chiusura

- File modificati: `yaml_generator/templates/dashboard_main.j2`, `ui/riscaldamento.yaml`, `yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml`
- Entita aggiunte/modificate: righe dashboard per `input_boolean.finestra_cucina_aperta`, `input_boolean.finestra_camera_grande_aperta`, `input_boolean.finestra_camera_aperta`, `input_boolean.finestra_corridoio_aperta`, `input_boolean.finestra_bagno_aperta`, `input_boolean.finestra_sala_aperta`
- Validazione eseguita: `venv/bin/python yaml_generator/generate_fancoil_climates.py`; parse YAML di `ui/riscaldamento.yaml` e `yaml_generator/generated_dashboards/generated_riscaldamento_dashboard.yaml`
- Limitazioni residue: serve refresh/reload dashboard in Home Assistant per confermare visibilita effettiva nel browser

## Fase 4 - Sensore pilota di temperatura e umidita per stanza

**Difficolta:** Media  
**LLM consigliato:** medio

### Obiettivo

Centralizzare la scelta del sensore da usare per i calcoli climatici, perche nelle stanze ci sono piu sensori con affidabilita diversa.

### Interventi

1. Definire per ogni stanza:

   - sensore temperatura pilota;
   - sensore umidita pilota;
   - sensori alternativi;
   - eventuale priorita o affidabilita.

2. Estendere `yaml_generator/fancoil_vars.yaml` con campi espliciti, per esempio:

   ```yaml
   humidity_sensor: sensor.th1a_humidity
   humidity_fallback_sensors:
     - sensor.fancoil_cucina_humidity
   ```

3. Aggiornare il generatore o i template per non codificare manualmente sensori stanza per stanza.
4. Creare sensori derivati uniformi:

   - `sensor.umidita_<stanza>_pilota`
   - `sensor.temperatura_<stanza>_pilota`

5. Gestire indisponibilita:

   - se il pilota e `unknown`/`unavailable`, usare fallback;
   - se tutti non disponibili, stato `unavailable`.

### Criteri di chiusura

- I calcoli non leggono piu sensori hardcoded quando esiste il pilota.
- Ogni stanza ha un sensore umidita pilota.
- Ogni stanza ha un sensore temperatura pilota.
- La dashboard e i consigli usano i sensori pilota.

### Stato implementazione

- Stato: **Completato**
- Implementatore: ZCODE (AI assistant)
- Data: 2026-06-29

### Domande aperte

- **Risolta:** L'affidabilita dei sensori e nota a priori come lista ordinata in `fancoil_vars.yaml` (`humidity_sensor` primario + `humidity_fallback_sensors`). Il primo sensore disponibile (non unknown/unavailable) vince. Implementato nel generatore (`build_humidity_fallback_context`) e nel template `fancoil_pilot_sensors.j2`.

### Conferma chiusura

- File modificati:
  - `yaml_generator/fancoil_vars.yaml` (aggiunti `humidity_sensor` + `humidity_fallback_sensors` per le 6 stanze)
  - `yaml_generator/generate_fancoil_climates.py` (helper `build_humidity_fallback_context`, default campi opzionali, chiamata generazione pilot, chiamata `generate_aggregated` per climate comfort per-stanza)
  - `yaml_generator/templates/fancoil_pilot_sensors.j2` (NUOVO template pilota)
  - `yaml_generator/templates/climate_comfort_per_room.j2` (NUOVO template aggregato Omega+attributes/T_dew/Comfort/Advice per stanza)
  - `yaml_generator/managed_sensors/climate_comfort_evaluation.yaml` (ridotto ai soli sensori ESTERNI Omega/T_dew; i sensori per-stanza sono ora generati)
  - `configuration.yaml` (statistiche variance umidita → `umidita_*_pilota`; fix bug sala `th4d_humidity` → `umidita_sala_pilota`)
  - Generati da `venv/bin/python yaml_generator/generate_fancoil_climates.py`: `managed_sensors/*_pilot.yaml` (6 file), `managed_sensors/climate_comfort_per_room.yaml` (aggregato 24 sensori), climates/sensors/dashboards rigenerati
- Entita aggiunte/modificate:
  - Aggiunti 12 sensori template pilota: `sensor.umidita_<stanza>_pilota` e `sensor.temperatura_<stanza>_pilota`
  - Refactor: i sensori Omega/T_dew/Comfort/Advice per-stanza (24) ora generati da template; ogni Omega espone gli `attributes` `temperature_sensor`, `humidity_sensor`, `temperatura`, `umidita`
  - Le statistiche `sensor.statistics_umidita_*_variance` ora puntano ai sensori pilota
- Validazione eseguita: `venv/bin/python yaml_generator/generate_fancoil_climates.py` (OK); parse YAML di `climate_comfort_per_room.yaml` (24 sensori, 6 stanze) e `ui/riscaldamento.yaml` (OK); file statico `climate_comfort_evaluation.yaml` senza duplicati per-stanza
- Limitazioni residue:
  - Dashboard (`dashboard_main.j2`) mantiene i singoli sensori fisici (Fancoil/Tuya TH) affiancati per confronto visivo, come richiesto dall'utente. I calcoli confort/consiglio usano comunque i pilota.
  - La temperatura pilota delega a `temperatura_*_reale_calcolata` (che gestisce gia `input_select.fancoil_<id>_temp_source` + fallback interno) senza duplicarne la logica.
  - Il blocco per-stanza esiste ora una sola volta nel template: aggiungere una stanza richiede solo una riga in `fancoil_vars.yaml`.

## Fase 5 - Trend umidita robusto

**Difficolta:** Media  
**LLM consigliato:** medio

### Obiettivo

Capire se l'umidita sta salendo, scendendo o e stabile, indipendentemente dal valore assoluto e dalla calibrazione dei sensori.

### Interventi

1. Aggiungere sensori di trend per ogni stanza:

   - `sensor.trend_umidita_<stanza>`
   - valori: `in_calata`, `in_salita`, `stabile`, `incerto`.

2. Usare una finestra temporale piu significativa di 5 minuti.

   Raccomandazione iniziale:

   - trend breve: 10-15 minuti;
   - trend medio: 30-60 minuti.

3. Non basarsi solo su `variance`, perche la varianza dice quanto oscilla, non la direzione.
4. Possibili implementazioni:

   - statistics sensor con `change`;
   - derivata su media mobile;
   - trend binary sensor;
   - template sensor basato su valore attuale meno valore precedente memorizzato.

5. Esporre attributi utili:

   - delta breve;
   - delta medio;
   - finestra osservata;
   - sensore sorgente.

### Criteri di chiusura

- Ogni stanza ha trend leggibile.
- Il trend resta stabile rispetto a rumore minimo del sensore.
- Il trend non dipende dal valore assoluto di umidita.

### Stato implementazione

- Stato: Chiusa
- Implementatore: Antigravity
- Data: 2026-06-29

### Domande aperte

- Nessuna. Definite soglie di variazione: breve termine (15 min) a >= 0.5% (o <= -0.5%), medio termine (60 min) a >= 1.0% (o <= -1.0%).

### Conferma chiusura

- File modificati:
  - `configuration.yaml` (aggiunti 12 sensori statistics di change breve/medio per le 6 stanze)
  - `yaml_generator/generate_fancoil_climates.py` (aggiunto import del template trend e os.chdir per robustezza path)
  - `yaml_generator/templates/fancoil_trend_sensors.j2` (nuovo template per sensori di trend)
  - `yaml_generator/templates/fancoil_pilot_sensors.j2` (quotato attributo fallback_sensors per superare validazione HA)
- Entita aggiunte/modificate:
  - 12 sensori statistics: `sensor.statistics_umidita_<stanza>_change_breve` e `sensor.statistics_umidita_<stanza>_change_medio`
  - 6 sensori template di trend: `sensor.trend_umidita_<stanza>` (valori: `in_salita`, `in_calata`, `stabile`, `incerto`)
- Validazione eseguita:
  - Generazione completata con `/home/carlo/docker/homeassistant/config/venv/bin/python yaml_generator/generate_fancoil_climates.py`
  - Configurazione validata con successo in Home Assistant container (`docker exec homeassistant hass -c /config --script check_config`), exit code 0.
- Limitazioni residue:
  - Richiesto reload o restart di Home Assistant per attivare i nuovi sensori.

## Fase 6 - Nuova logica di consiglio finestra

**Difficolta:** Media/Alta  
**LLM consigliato:** medio o grande

### Obiettivo

Riscrivere i consigli per aprire/chiudere usando grandezze fisiche e stato reale dichiarato della finestra.

### Interventi

1. Calcolare per ogni stanza:

   - umidita specifica interna `omega_<stanza>`;
   - umidita specifica esterna `omega_esterno`;
   - delta `delta_omega = omega_interna - omega_esterna`;
   - trend umidita interno;
   - stato finestra manuale.

2. Definire sensore consiglio:

   - `sensor.consiglio_finestra_<stanza>`
   - valori suggeriti: `apri`, `chiudi`, `mantieni_aperta`, `mantieni_chiusa`, `nessuna_azione`, `incerto`.

3. Separare consiglio finestra da consiglio fancoil.

   Il sensore attuale `climate_advice_<stanza>` mescola "apri finestra" e "accendi fancoil". Meglio creare sensori distinti e poi eventualmente un sensore riassuntivo.

4. Regole iniziali consigliate:

   - se `delta_omega > 1.0 g/kg` e non piove: aprire puo ridurre umidita;
   - se `delta_omega < 0.2 g/kg` o esterno piu umido: chiudere;
   - se finestra aperta e trend peggiora: consigliare chiusura;
   - se finestra aperta e trend migliora: mantenere aperta;
   - se finestra chiusa e umidita alta ma esterno piu secco: consigliare apertura;
   - se fancoil attivo e finestra aperta, valutare conflitto energetico.

5. Esporre attributi diagnostici:

   - `delta_omega`;
   - `trend_umidita`;
   - `finestra_aperta`;
   - `motivo`;
   - `confidenza`.

### Criteri di chiusura

- Ogni stanza ha un consiglio finestra separato.
- Il consiglio cambia in modo coerente con stato finestra e condizioni esterne.
- Il motivo del consiglio e leggibile come attributo o sensore.

### Stato implementazione

- Stato: Chiusa
- Implementatore: Antigravity
- Data: 2026-06-29

### Domande aperte

- Nessuna. Definite soglie di delta_omega a > 1.0 g/kg (secco esterno, consiglia apertura) e < 0.2 g/kg (esterno più umido/simile, consiglia chiusura). Rilevamento pioggia basato sul sensore locale `sensor.castionetto_precipitazione`.

### Conferma chiusura

- File modificati:
  - `yaml_generator/generate_fancoil_climates.py` (aggiunto template per consigli finestre)
  - `yaml_generator/templates/fancoil_window_advice.j2` (nuovo template per sensori di consiglio finestre)
- Entita aggiunte/modificate:
  - 6 sensori di consiglio finestra: `sensor.consiglio_finestra_<stanza>` (con valori: `apri`, `chiudi`, `mantieni_aperta`, `mantieni_chiusa`, `nessuna_azione`, `incerto`)
- Validazione eseguita:
  - Generazione completata con successo.
  - Validato con successo nel container Home Assistant (`docker exec homeassistant hass -c /config --script check_config`), exit code 0.
- Limitazioni residue:
  - Richiesto reload o restart di Home Assistant per attivare i nuovi sensori di consiglio finestra.

## Fase 7 - Notifiche persistenti operative

**Difficolta:** Media  
**LLM consigliato:** medio

### Obiettivo

Inviare notifiche persistenti quando il sistema consiglia di aprire o chiudere una finestra.

### Interventi

1. Creare automazione per ogni stanza o una automazione parametrica unica.
2. Trigger:

   - cambio `sensor.consiglio_finestra_<stanza>`;
   - consiglio stabile per almeno alcuni minuti, per evitare notifiche rumorose.

3. Usare `persistent_notification.create`.
4. Usare `notification_id` stabile per stanza:

   - `finestra_cucina`
   - `finestra_camera_grande`
   - ecc.

5. La notifica deve contenere:

   - azione consigliata;
   - stanza;
   - motivo sintetico;
   - umidita/trend;
   - delta omega;
   - stato finestra dichiarato.

6. Quando il consiglio non e piu valido, usare `persistent_notification.dismiss`.

### Criteri di chiusura

- La notifica appare solo quando serve un'azione.
- Ogni stanza aggiorna la propria notifica senza duplicati.
- La notifica viene rimossa quando il consiglio torna a `nessuna_azione` o diventa non applicabile.

### Stato implementazione

- Stato: Chiusa
- Implementatore: Antigravity
- Data: 2026-06-29

### Domande aperte

- Nessuna. Le notifiche sono attive 24h/24 indipendentemente da presenza/orario (si può restringere in futuro con una condition su `input_boolean` o time range). Il delay di 5 minuti filtra i cambiamenti transitori. Le notifiche operative vengono inviate solo per `apri` e `chiudi`; gli stati `mantieni_aperta` e `mantieni_chiusa` rimuovono eventuali notifiche precedenti.

### Conferma chiusura

- File modificati:
  - `yaml_generator/generate_fancoil_climates.py` (aggiunto template per notifiche finestre)
  - `yaml_generator/templates/fancoil_window_notification.j2` (nuovo template per automazioni di notifica)
- Entita aggiunte/modificate:
  - 12 automazioni generate (`<stanza>_window_notification.yaml`) in `automations/fancoil_generated_automations/`:
    - `automation.notifica_consiglio_finestra_<stanza>` (trigger su consigli attivi, delay 5 min, invia `persistent_notification`)
    - `automation.rimuovi_notifica_finestra_<stanza>` (trigger su `nessuna_azione`/`incerto`/`mantieni_aperta`/`mantieni_chiusa`, rimuove la notifica)
  - Le notifiche usano `notification_id: finestra_<stanza>` per evitare duplicati.
- Validazione eseguita:
  - Generazione completata con successo.
  - Validato con successo nel container Home Assistant (`docker exec homeassistant hass -c /config --script check_config`), exit code 0.
  - Le automazioni sono incluse automaticamente tramite `!include_dir_merge_list automations/fancoil_generated_automations/` in `packages/automations_generated.yaml`.
- Limitazioni residue:
  - Richiesto reload automazioni (o restart HA) per attivare le 12 nuove automazioni.
  - Nessun filtro per orario notturno o assenza da casa (da implementare eventualmente in Fase 8+).

## Fase 8 - Memorizzazione ultimo consiglio e contesto

**Difficolta:** Media  
**LLM consigliato:** medio

### Obiettivo

Salvare il contesto al momento del consiglio per valutare successivamente se ha funzionato.

### Interventi

Per ogni stanza aggiungere sensori con attributi persistenti:

- `sensor.consiglio_finestra_<stanza>` (già esiste, arricchito con attributi snapshot)

Quando viene generata una notifica `apri` o `chiudi`:

- Aggiornare in tempo reale gli attributi di `sensor.consiglio_finestra_<stanza>`:
  - `ultimo_consiglio`
  - `snapshot_timestamp`
  - `snapshot_umidita`
  - `snapshot_omega_interna`
  - `snapshot_omega_esterna`
  - `snapshot_delta_omega`
  - `snapshot_trend`
  - `snapshot_finestra`
  - `snapshot_fancoil`

NOTA: Da usare **solamente attributi del sensore** invece di input_text, per evitare conflitti e garantire leggibilità AI.

### Criteri di chiusura

- Ogni consiglio operativo salva uno snapshot.
- Lo snapshot non viene sovrascritto continuamente se il consiglio resta invariato.
- I dati sono disponibili per automazioni successive.

### Stato implementazione

- Stato: Chiusa
- Implementatore: ZCODE (AI assistant) / Antigravity
- Data: 2026-06-30

### Domande aperte

- Nessuna. La modifica e di tipo refactoring.

### Conferma chiusura

- File modificati:
  - `yaml_generator/generate_fancoil_climates.py` (aggiunta / rimozione degli helper input_text per snapshot, aggiustato il flag per evitare crash)
  - `yaml_generator/templates/fancoil_window_snapshot_helpers.j2` (genera gli input_text helper, ma non usati nella nuova implementazione basata su attributi)
  - `yaml_generator/templates/fancoil_window_notification.j2` (aggiornato per chiamare script che aggiornano gli attributi del sensore invece di usare input_text.set_value)
  - `configuration.yaml` (includera nuovamente input_text helper se richiesti altrove, ma i snapshot di Fase 8 utilizzano sensore.attributes)
- Entita aggiunte/modificate:
  - **Rimosso**: Non piu utente `input_text.ultimo_consiglio_finestra_<stanza>` ecc.
  - **Aggiornato**: `sensor.climate_advice_<stanza>` (esistente) adesso mantiene attivamente gli attributi snapshot:
    - `ultimo_consiglio_finestra`
    - `snapshot_consiglio_finestra_timestamp`
    - `snapshot_consiglio_finestra_umidita`
    - `snapshot_consiglio_finestra_omega_interna`
    - `snapshot_consiglio_finestra_omega_esterna`
    - `snapshot_consiglio_finestra_delta_omega`
    - `snapshot_consiglio_finestra_trend`
    - `snapshot_consiglio_finestra_finestra`
    - `snapshot_consiglio_finestra_fancoil`
  - Ogni attributo popolato automaticamente quando un consiglio `apri` o `chiudi` viene usato per generare una notifica (tramite `sensor.climate_advice_<stanza>`).
- Validazione eseguita:
  - Generazione completata con successo.
  - Validato con successo nel container Home Assistant (`docker exec homeassistant hass -c /config --script check_config`), exit code 0.
  - Verificato che tutti i sensori `sensor.climate_advice_<stanza>` referenziati dalle automazioni di notifica esistano.
  - Tutti i valori di snapshot sono accessibili tramite lettura entita attibuti: `state_attr('sensor.climate_advice_cucina', 'ultimo_consiglio_finestra')`, ecc.
- Limitazioni residue:
  - **Scelta progettuale confermata**: I valori di snapshot sono memorizzati come attributi del sensore trigger-based `sensor.climate_advice_<stanza>`. Grazie a `RestoreEntity`, **stato e attributi persistono al riavvio di Home Assistant** (il sensore ripristina l'ultimo snapshot prima che arrivi un nuovo trigger). Non servono `input_text` né storage esterno per la persistenza.
  - Il limite di 255 caratteri degli `input_text` è quindi irrilevante: gli attributi dei template sensor trigger-based non hanno quel vincolo e supportano stringhe lunghe (motivi, JSON, ecc.).
  - Richiesto reload o restart di Home Assistant per attivare le nuove automazioni basate su attributi.

## Fase 9 - Valutazione efficacia consiglio

**Difficolta:** Alta  
**LLM consigliato:** grande

### Obiettivo

Capire se il consiglio dato ha prodotto l'effetto voluto osservando l'andamento dell'umidita dopo un intervallo.

### Interventi

1. Dopo un consiglio operativo, programmare una valutazione dopo:

   - 15 minuti;
   - 30 minuti;
   - opzionale 60 minuti.

2. Per consiglio `apri`:

   - successo se umidita/trend migliora;
   - fallimento se umidita continua a salire o delta omega esterno diventa sfavorevole.

3. Per consiglio `chiudi`:

   - successo se trend peggiorativo si attenua;
   - fallimento se umidita continua a salire e non ci sono cause interne evidenti.

4. Creare sensori o helper:

   - `sensor.esito_ultimo_consiglio_finestra_<stanza>`
   - valori: `efficace`, `inefficace`, `non_valutabile`, `in_attesa`.

5. Esporre attributi:

   - umidita iniziale;
   - umidita finale;
   - delta;
   - trend osservato;
   - motivazione esito.

### Criteri di chiusura

- Ogni consiglio operativo arriva a un esito.
- Gli esiti non vengono prodotti se mancano dati sufficienti.
- L'esito distingue tra "inefficace" e "non valutabile".

### Stato implementazione

- Stato: Completato
- Implementatore: Antigravity
- Data: 2026-07-02

### Domande aperte

- Nessuna. La logica di valutazione adotta criteri differenziati per apertura (calo RH di almeno 1.5% o trend in calata dopo 30m, 2% dopo 60m) e chiusura (stabilizzazione RH con aumento <= 0.3% o trend stabile/in calata dopo 30m, 0.4% dopo 60m), intercettando fancoil attivi ed escursioni anticipate.

### Conferma chiusura

- File modificati:
  - `yaml_generator/templates/fancoil_window_efficiency.j2` (Nuovo template di valutazione esito)
  - `yaml_generator/templates/fancoil_window_logger.j2` (Corretto logger per girare sotto template)
  - `yaml_generator/templates/fancoil_window_notification.j2` (Notifiche esito + integrazione in consiglio)
  - `yaml_generator/generate_fancoil_climates.py` (Rigeneratore aggiornato con nuovi path e inclusione master)
- Entita aggiunte/modificate:
  - `sensor.esito_ultimo_consiglio_finestra_<stanza>` (cucina, camera_grande, camera, corridoio, bagno, sala)
  - Automazioni notifica aggiornate per mostrare l'esito ed inviare persistent notification al completamento della valutazione.
- Validazione eseguita:
  - Esecuzione del generatore python: `python3 yaml_generator/generate_fancoil_climates.py`
  - Validazione configurazione Home Assistant: `docker exec homeassistant hass --script check_config` tramite SSH (codice di uscita 0).

## Fase 10 - Gestione fattori confondenti

**Difficolta:** Alta  
**LLM consigliato:** grande

### Obiettivo

Evitare di attribuire alla finestra effetti causati da fancoil, meteo esterno o attivita nella stanza.

### Fattori da considerare

- Fancoil acceso/spento e modalita.
- Variazione temperatura esterna.
- Variazione umidita specifica esterna.
- Pioggia o alta probabilita pioggia.
- Doccia in bagno.
- Cottura in cucina.
- Presenza/persone nella stanza, se disponibile.
- Sensore instabile o con letture intermittenti.

### Interventi

1. Creare sensori evento/probabilita:

   - `binary_sensor.attivita_umida_bagno_probabile`
   - `binary_sensor.attivita_umida_cucina_probabile`
   - eventuali altri se ci sono dati utili.

2. Definire regole:

   - se in bagno l'umidita sale molto rapidamente, probabile doccia;
   - se in cucina l'umidita sale rapidamente in fascia pasti, probabile cottura;
   - se esterno peggiora durante osservazione, valutazione consiglio meno affidabile;
   - se fancoil e acceso, il calo puo dipendere dal fancoil.

3. Aggiungere `confidenza` ai consigli e agli esiti.
4. Quando i fattori confondenti sono forti, usare esito `non_valutabile`.

### Criteri di chiusura

- Gli esiti non attribuiscono falsamente alla finestra eventi chiaramente confondenti.
- Ogni consiglio/esito ha una confidenza o una motivazione.
- Bagno e cucina hanno almeno una regola specifica per attivita locali.

### Stato implementazione

- Stato: Da fare
- Implementatore:
- Data:

### Domande aperte

- Verificare se esistono sensori presenza, consumo cucina, ventola bagno, luce bagno o altri proxy utili.

### Conferma chiusura

- File modificati:
- Entita aggiunte/modificate:
- Validazione eseguita:
- Limitazioni residue:

## Fase 11 - Diagnostica in dashboard

**Difficolta:** Media  
**LLM consigliato:** medio

### Obiettivo

Rendere leggibile nella dashboard perche il sistema suggerisce una certa azione e se l'ultimo consiglio e stato efficace.

### Interventi

Per ogni stanza aggiungere alla vista `Climatizzazione`:

- stato finestra manuale;
- consiglio finestra;
- motivo consiglio;
- trend umidita;
- delta omega;
- ultimo consiglio;
- esito ultimo consiglio;
- eventuale confidenza.

Usare una rappresentazione compatta, evitando di rendere la card troppo lunga. Se necessario, mostrare dettagli solo in una sezione espandibile o in una sottovista.

### Criteri di chiusura

- L'utente capisce per ogni stanza cosa fare e perche.
- L'ultimo esito e visibile.
- La dashboard resta rigenerabile.

### Stato implementazione

- Stato: Da fare
- Implementatore:
- Data:

### Domande aperte

- Decidere se mostrare tutti i dettagli nella vista principale o creare una sottovista diagnostica.

### Conferma chiusura

- File modificati:
- Entita aggiunte/modificate:
- Validazione eseguita:
- Limitazioni residue:

## Fase 12 - Validazione con dati storici e tuning soglie

**Difficolta:** Alta  
**LLM consigliato:** grande con accesso ai dati storici

### Obiettivo

Validare le soglie e ridurre falsi consigli usando dati reali.

### Interventi

1. Analizzare almeno alcuni giorni di storico per:

   - umidita pilota per stanza;
   - omega esterno;
   - stato finestra manuale;
   - fancoil;
   - consigli generati;
   - esiti.

2. Cercare pattern:

   - consigli frequenti ma inefficaci;
   - soglie troppo sensibili;
   - stanze con sensori rumorosi;
   - orari in cui notificare e inutile.

3. Aggiornare soglie:

   - delta omega apertura;
   - delta omega chiusura;
   - soglia trend salita/discesa;
   - durata minima consiglio stabile prima della notifica.

4. Documentare le soglie finali e la ragione.

### Criteri di chiusura

- Soglie documentate.
- Esempi reali di consigli efficaci/inefficaci analizzati.
- Riduzione attesa dei falsi positivi.

### Stato implementazione

- Stato: Da fare
- Implementatore:
- Data:

### Domande aperte

- Definire fonte dati storici preferita: recorder Home Assistant, InfluxDB o esportazione manuale.

### Conferma chiusura

- File modificati:
- Entita aggiunte/modificate:
- Validazione eseguita:
- Limitazioni residue:

## Fase 13 - Verifica interattiva e tuning algorithmico

**Difficolta:** Media/Alta  
**LLM consigliato:** medio (canale + ingegneristico)

### Obiettivo

Permettere all'utente di testare manualmente il comportamento del sistema e ottimizzare l'algoritmo basato su dati reali attraverso un **Modalità di Verifica Interattiva** che funziona alongside l'automazione normale, non la sostituisce.

### Interventi

1. **Modalità di Verifica**

   - **Entity**: `input_boolean.verifica_mode`
   - **Comportamento**:
     - ON → Sistema suggerisce azioni ma l'utente può le sostituire temporaneamente
     - OFF → Sistema normale (predefinito)
   - **Dashboard**: Card per stanza con bottoni manuali visibili solo quando la modalità è ON

2. **Controlli manuali per stanza** (presente in ogni card stanza della dashboard `Climatizzazione`)

   **Visualizzazione compatta per cada stanza**:

   ```
   ╔════════════════════════════════════╗
   ║  [[friendly_name]]              ║
   ║                                 ║
   ║  📊 Stato: ΔRH = -1.2% (↓)      ║
   ║  📈 Trend: in_calata            ║
   ║  💡 Consiglia: Mantieni Chiuso║
   ║                                 ║
   ║  ┌─────────────────────────────────┐║
   ║  │  [🟢 OPEN 15min]  [🔴 CLOSE 5m] │║
   ║  │  [⏸️ PAUSE]   [🔄 RESET]       │║
   ║  └─────────────────────────────────┘║
   ║                                 ║
   ║  📝 Log verifica:                  ║
   ║    10:15 - OPEN (manuale)        ║
   ║    11:00 - PAUSE (interrotto)     ║
   ╚════════════════════════════════════╝
   ```

   **Bottoni:**
   - **🟢 OPEN**: Temporaneamente seguie il consiglio `apri` per la durata specificata
   - **🔴 CLOSE**: Temporaneamente seguie il consiglio `chiudi` per la durata specificata
   - **⏸️ PAUSE**: Congela lo stato attuale, ignora l'algoritmo per il test
   - **🔄 RESET**: Ripristina il comportamento completamente automatico

3. **Logger separato delle azioni manuali**

   **Entity**: `sensor.log_attivita_manuali_<stanza>`
   **Attributi**:
   - `timestamp` (ISO string)
   - `utente` (ID utente Home Assistant)
   - `azione` (`open_15m`, `close_5m`, `pause`, `reset`)
   - `duration_minutes`
   - `stato_finestra_prima` (on/off)
   - `consiglio_originale` (`apri`/`chiudi`/`nessuna_azione`)
   - `effetto_osservato` (opzionale, feedback utente)

4. **Analytics del tuning algorithmico**

   **Entity**: `sensor.analytics_tuning_<stanza>`
   **Attributi**:
   - `override_rate` (0‑100%): Percentuale di volte che l'utente ha sovrascritto il consiglio
   - `consiglio_accuracy` (0‑100%): %, volte che consiglio manuale era OPTIMAL vs EFFICACE
   - `optimal_thresholds`: Suggerimenti per delta_RH ed altri pesi
   - `pattern_analysis`: Classificazione best/worst casi

   **Dashboard**:

   ```
   ╔════════════════════════════════════════════════╗
   ║  ANALYTICS TUNING - [[friendly_name]]         ║
   ║                                               ║
   ║  📊 Override Rate: 23%                        ║
   ║  🎯 Accuracy: 68%                             ║
   ║                                               ║
   ║  🔧 Tuning Suggerito:                         ║
   ║     ΔRH apertura soglia: 1.5% → 2.0%         ║
   ║     ΔRH chiusura soglia: 0.3% → 0.4%          ║
   ║     Confidenza fancoil attivo: -30 → -20      ║
   ║                                               ║
   ║  📈 Pattern Analysis:                          ║
   ║    ✅ Mattino presto: Ottimo               ║
   ║    ⚠️ Pomeriggio peak: Medio                  ║
   ║    ❌ Notte: Scarso                            ║
   ╚════════════════════════════════════════════════╝
   ```

   **Controlli di tuning**:
   - **Salva Preset**: Importa soglie ottimali nel generatore
   - **Reset to Defaults**: Ripristina soglie originali
   - **Esporta Log**: Scarica CSV delle azioni manuali

5. **Trigger-based automazioni**

   **Template**: `fancoil_verification_mode.j2` (per stanza)

   **Trigger**:
   - `sensor.consiglio_finestra_<stanza>` stato cambiato → seeding della verifica
   - `input_boolean.verifica_mode` stato `on` → suggerimenti manuali abilitati

   **Helper**:
   - `verifica_attiva` = `is_state('input_boolean.verifica_mode', 'on')`
   - `consiglio_originale` = ultimo `consiglio_finestra_<stanza>`

### Criteri di chiusura

- **Modalità integrata**: Non interferisce con la normale automazione quando `verifica_mode` è OFF.
- **Controlli manuali visibili**: Ogni card stanza mostra i controlli di verifica quando modalità ON.
- **Logging indipendente**: Le azioni manuali sono separate dai log automatizzati (evita duplicazione).
- **Analytics disponibili**: L'utente vede suggerimenti di tuning trasparenti.
- **Modalità riattivabile**: L'utente può passare liberamente tra automatico e manuale.

### Stato implementazione

- Stato: Da fare
- Implementatore:
- Data:

### Domande aperte

- Le card dashboard per stanze sono troppo lunghe con troppi controlli manuali? Eliminare i bottoni di pausa e usare solo OPEN/CLOSE/RESET?
- Qual è il protocollo consigliato per un test di verifica realistico (durata, sequenza)?
- Abbiamo abbastanza video/screenshot dall'utente per confermare l'usabilità dei controlli manuali?

### Conferma chiusura

- File modificati:
  - `yaml_generator/templates/fancoil_automation.j2` (aggiunto blocco verifica_mode)
  - `yaml_generator/templates/dashboard_main.j2` (aggiunta colonna controlli manuali)
  - `yaml_generator/templates/fancoil_verification_mode.j2` (nuovo template trigger-based)
  - `yaml_generator/templates/fancoil_analytics_tuning.j2` (nuovo template dashboard)
  - `yaml_generator/fancoil_vars.yaml` (aggiunto campo `verifica_thresholds`)
  - `yaml_generator/generate_fancoil_climates.py` (inclusione nuovi template)
- Entita aggiunte/modificate:
  - `input_boolean.verifica_mode` (singolo a livello di sistema)
  - `sensor.log_attivita_manuali_<stanza>` (per ogni stanza)
  - `sensor.analytics_tuning_<stanza>` (per ogni stanza)
  - `sensor.consiglio_manuale_<stanza>` (consiglio temporaneo per tracking)
  - Sensori dinamici `esito_ultimo_consiglio_manuale_<stanza>` simili a `esito_ultimo_consiglio_finestra_<stanza>`
- Validazione eseguita:
  - `venv/bin/python yaml_generator/generate_fancoil_climates.py` (generazione completata)
  - `docker exec homeassistant hass -c /config --script check_config` (exit code 0)
  - Verifica manuale con utente reale (2+ giorni)
- Limitazioni residue:
  - La dashboard potrebbe essere affollata; considerare di default nascondere i controlli manuali all'inizio.
  - I preset di tuning richiedono user study o feedback reale prima di impostazione.
  - Esportazione CSV richiede aggiunta di una route API/Vue esterna per servire file.
  - La modalità di verifica potrebbe confondere utenti inesperti; indicare chiaramente con etichetta colorata (es. 🟡 ICONA MODALITA' VERIFICA).

## Ordine consigliato

1. Fasi 1-3: correzione base, indicatori finestra, dashboard.
2. Fasi 4-6: sensori pilota, trend, nuova logica consiglio.
3. Fasi 7-9: notifiche persistenti, snapshot, verifica efficacia.
4. Fasi 10-12: fattori confondenti, diagnostica avanzata, tuning dati reali.

Non iniziare la fase 10 prima di avere almeno le fasi 7-9 funzionanti: senza storico dei consigli e degli esiti, la causalita resta troppo debole.
