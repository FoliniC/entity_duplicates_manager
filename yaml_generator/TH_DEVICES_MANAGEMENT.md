# Gestione Dispositivi TH (Tuya Temperature & Humidity)

Questo documento descrive l'architettura e il funzionamento del sistema di gestione dei sensori Tuya a batteria (serie `th*`: th1a, th2b, th3c, th4d), progettato per garantire persistenza dei dati e monitoraggio dello stato energetico.

## 1. Architettura del Sistema

I sensori Tuya a batteria trasmettono dati solo su variazione significativa per preservare la carica. Il sistema utilizza un approccio basato su **Trigger-based Template Sensors** per eliminare i problemi di entità `unavailable` o `unknown` al riavvio di Home Assistant.

### Livello 1: Trigger-based Persistence (Operativo e Persistente)
Le entità principali sono definite come sensori template con trigger. Reagiscono ai cambiamenti dei sensori fisici Tuya e all'avvio di Home Assistant.
- **File:** `yaml_generator/managed_persistence/th_persistence.yaml`
- **Entità:** `sensor.th*_temperature`, `sensor.th*_humidity`, `sensor.th*_battery`
- **Logica:** 
  - Al riavvio o su trigger, se il sensore fisico non è disponibile, il sensore mantiene il suo stato precedente (`this.state`).
  - Questo elimina la dipendenza dalle query SQL dirette al database per il ripristino dei valori.

### Livello 2: Monitoraggio Batteria (Livello di Manutenzione)
Sensori binari che gestiscono la natura eterogenea dei dati Tuya (alcuni inviano %, altri stringhe come "low").
- **File:** `yaml_generator/managed_binary_sensors/th_battery_alerts.yaml`
- **Logica:** 
  - Allerta se valore numerico < 20%
  - Allerta se valore testuale è "low" o "empty"

## 2. Automazione e Generazione

Il sistema è semi-automatizzato per facilitare l'aggiunta di nuovi sensori.

### Script di Generazione: `helpers/generate_sensors.py`
Questo script Python è il "motore" del sistema. Quando viene eseguito, rigenera i file di configurazione YAML basandosi sulla lista `devices`.
- Genera i sensori di persistenza trigger-based.
- Aggiorna i sensori binari per le batterie.
- (Legacy) Poteva generare sensori SQL, ora sostituiti dalla logica trigger.

### Notifiche Persistenti
L'automazione in `automations/th_battery_alerts.yaml` monitora i sensori di batteria e genera una **Persistent Notification** nella UI di Home Assistant quando è necessario un intervento umano.

## 3. Manutenzione

Per aggiungere un nuovo sensore (es. `th5e`):
1. Aprire `helpers/generate_sensors.py`.
2. Aggiungere `{"id": "th5e", "area": "nome_stanza"}` alla lista `devices`.
3. Eseguire lo script (o attendere la generazione automatica se prevista).
4. Ricaricare le configurazioni Template e SQL in Home Assistant.

---
*Ultimo aggiornamento: 31 Maggio 2026*
