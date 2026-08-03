# Sistema climatizzazione fancoil

Questo documento descrive la logica generata da `yaml_generator/generate_fancoil_climates.py` per il sistema di climatizzazione a fancoil.

## Sorgenti e file generati

La configurazione delle stanze parte da `yaml_generator/fancoil_vars.yaml`.

I template principali sono:

- `yaml_generator/templates/fancoil_automation.j2`: automazioni stanza, calcolo velocita, guardie globali, recovery.
- `yaml_generator/templates/fancoil_climate.j2`: climate template per ogni stanza.
- `yaml_generator/templates/fancoil_sensors.j2`: sensori di supporto per temperatura, delta e modalita.
- `yaml_generator/templates/fancoil_binary_sensors.j2`: sensori binari di stop e stato.
- `yaml_generator/templates/fancoil_master_input_booleans.j2`: helper booleani master.
- `yaml_generator/templates/fancoil_room_input_*`: helper per stanza.

I file operativi generati sono in:

- `automations/fancoil_generated_automations/*_automation.yaml`
- `yaml_generator/generated_climates/`
- `yaml_generator/managed_sensors/`
- `yaml_generator/managed_binary_sensors/`
- `yaml_generator/input_boolean/`, `input_number/`, `input_select/`, `input_datetime/`, `input_text/`

Le modifiche manuali alla logica stanza vanno fatte nel template `.j2`, poi si rigenerano i file. Modificare solo i file generati espone al rischio di perdere le correzioni alla generazione successiva.

## Entita globali

Le entita globali principali sono:

- `switch.attiva_fancoil`: consenso generale ai fancoil.
- `switch.attiva_pdc`: consenso PDC.
- `switch.attiva_pompa_circolazione`: consenso pompa circolazione.
- `input_select.fancoil_system_hvac_mode`: modalita master del sistema (`heat`, `cool`, `dry`, `off`).
- `input_boolean.fancoil_deumidificazione`: abilita il comportamento di deumidificazione.
- `binary_sensor.pdc_acqua_calda`: blocco/limitazione quando l'acqua PDC e calda.
- `binary_sensor.fancoil_circuit_temp_invalid`: stato temperatura circuito non valida.

## Rilevamento automatico finestra cucina

La cucina utilizza un sensore di contatto automatico `binary_sensor.contact_sensor_doorcontact_state` per rilevare lo stato della finestra, eliminando la necessità dell'`input_boolean.finestra_cucina_aperta` manuale.

Il sensore comunica di sua iniziativa solo quando la porta della finestra viene aperta o chiusa. In condizioni normali il sensore risulta non accessibile (unavailable).

Quando `window_contact_sensor` è definito per una stanza in `fancoil_vars.yaml`:

- non viene creato l'`input_boolean.finestra_<stanza>_aperta`;
- tutte le automazioni e i sensori usano il `binary_sensor` di contatto come sorgente dello stato finestra;
- il dashboard mostra lo stato del sensore di contatto direttamente.

## `system_enabled`

`system_enabled` e una variabile interna alle automazioni stanza, non una entity Home Assistant.

Vale `true` solo quando tutte queste condizioni sono vere:

```jinja
is_state('switch.attiva_fancoil', 'on')
and is_state('switch.attiva_pdc', 'on')
and is_state('switch.attiva_pompa_circolazione', 'on')
```

Quando `system_enabled=false`:

- il target ventola stanza diventa `off`;
- le automazioni spengono i quattro rele a valle (`switch_1..4`);
- il `fan_mode` del climate stanza viene portato a `off`;
- init e resume delle velocita vengono fermati;
- lo Stox principale resta alimentato, per mantenere disponibili temperatura e umidita.

## Stox e rele stanza

Ogni stanza ha uno switch principale:

```text
switch.stox_fancoil_<stanza>_switch
```

Questo alimenta il device con i quattro rele e deve restare acceso in condizioni normali, anche quando `system_enabled=false`, per continuare a leggere temperatura e umidita.

I quattro rele stanza sono:

```text
switch.fancoil_<stanza>_switch_1
switch.fancoil_<stanza>_switch_2
switch.fancoil_<stanza>_switch_3
switch.fancoil_<stanza>_switch_4
```

La mappa hardware delle velocita e:

```text
[0,0,0,0] = off
[0,0,0,1] = idle
[1,0,0,1] = low
[0,1,0,1] = medium
[0,0,1,1] = high
altro     = unknown
```

Quando il sistema globale e disabilitato, tutti i quattro rele devono essere `off`. Lo Stox principale invece non viene spento dalla guardia globale.

## Calcolo del target ventola

Il target stanza viene calcolato da:

- modalita stanza (`sensor.fancoil_<stanza>_hvac_temp_mode`);
- differenza temperatura/setpoint (`sensor.fancoil_<stanza>_temperature_difference`);
- soglie `input_number.fan_distance_*`;
- stop condition;
- deumidificazione;
- stato acqua calda PDC;
- `system_enabled`.

La prima guardia e `system_enabled`: se e falso, il target e `off` indipendentemente dal delta temperatura.

## Inizializzazione e reload

Le automazioni stanza reagiscono a:

- cambi di sensori stanza;
- cambi di `switch.attiva_fancoil`, `switch.attiva_pdc`, `switch.attiva_pompa_circolazione`;
- evento `automation_reloaded`;
- evento `fancoil_start_initialization`;
- trigger periodico da 10 minuti.

Al reload o al riavvio, se il sistema globale non e abilitato, la guardia globale spegne i rele a valle e ferma l'automazione prima di init/resume.

## Recovery e power cycle Stox

La recovery `Ripristino anomalie (Temp/Speed)` puo spegnere e riaccendere lo Stox per 10 secondi.

Questo comportamento e intenzionale: serve a recuperare casi in cui il device con i rele non risponde correttamente. La recovery non deve essere bloccata da `system_enabled=false`.

I casi gestiti sono:

- `temp_stuck`: temperatura ferma mentre la stanza dovrebbe lavorare e la velocita hardware e `low`, `medium` o `high`;
- `speed_mismatch`: target diverso dallo stato hardware per un tempo prolungato;
- `global_disabled_hw_stuck`: sistema globale disabilitato ma rele hardware ancora diversi da `off`.

Nel caso `global_disabled_hw_stuck`, la recovery puo comunque ciclare lo Stox per sbloccare il device, anche se normalmente lo Stox deve restare acceso.

## Logging

Gli eventi fancoil sono scritti tramite evento `fancoil_log_event`, gestito dal sistema HALog2026 documentato in `logs/HALOG2026_README.md`.

Il log operativo principale e:

```text
logs/fancoil_events/fancoil_events.log
```

I messaggi rilevanti per questa logica includono:

- `State Dump`: fotografia del calcolo stanza, con `Target`, `System`, `Main` e stato rele.
- `GLOBAL DISABLED: Stox acceso...`: lo Stox viene mantenuto alimentato.
- `GLOBAL DISABLED: spengo rele stanza...`: i quattro rele a valle vengono spenti.
- `FORCE MAIN ON`: lo Stox viene riacceso per mantenere disponibili temperatura/umidita.
- `Ripristino anomalia ... Avvio Power Cycle Stox`: recovery attiva.

## Note operative

`switch.attiva_pdc` e `switch.attiva_pompa_circolazione` sono switch KNX. Se la dashboard mostra uno stato non coerente subito dopo il riavvio, fare refresh della pagina prima di assumere un errore di automazione.

Se lo stato Home Assistant non corrisponde allo stato fisico KNX, verificare la configurazione `state_address` degli switch KNX in `knx_config.yaml`.
