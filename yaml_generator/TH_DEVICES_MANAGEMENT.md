# Gestione Dispositivi TH (Tuya Temperature & Humidity)

Questo documento descrive l'architettura e il funzionamento del sistema di gestione dei sensori Tuya a batteria (serie `th*`: th1a, th2b, th3c, th4d), progettato per garantire persistenza dei dati e monitoraggio dello stato energetico.

## 1. Architettura del Sistema

I sensori Tuya a batteria trasmettono dati solo su variazione significativa per preservare la carica. Il sistema utilizza un approccio a tre livelli per eliminare i problemi di entità `unavailable` o `unknown` al riavvio di Home Assistant.

### Livello 1: SQL Persistence (Livello di Recupero)
I sensori SQL interrogano direttamente il database MariaDB per recuperare l'ultimo valore numerico valido registrato.
- **File:** `sql_sensors/sql_sensors.yaml`
- **Entità:** `sensor.th*_temperature_humidity_*_last`
- **Scopo:** Fornire un valore di fallback immediato dopo il riavvio di HA, prima che il sensore fisico trasmetta nuovi dati.

### Livello 2: Template Sensors (Livello Operativo)
Le entità principali utilizzate nelle automazioni e nella UI applicano una logica di scelta:
- **Priorità 1:** Valore "Live" dal sensore Tuya (se numerico e valido).
- **Priorità 2:** Valore "SQL" (se il sensore Tuya è `unavailable` o `unknown`).
- **File:** `managed_sensors/template_sensors.yaml`
- **Entità:** `sensor.th1a_temperature`, `sensor.th1a_humidity`, ecc.

### Livello 3: Monitoraggio Batteria (Livello di Manutenzione)
Sensori binari che gestiscono la natura eterogenea dei dati Tuya (alcuni inviano %, altri stringhe come "low").
- **File:** `yaml_generator/managed_binary_sensors/th_battery_alerts.yaml`
- **Logica:** 
  - Allerta se valore numerico < 20%
  - Allerta se valore testuale è "low" o "empty"

## 2. Automazione e Generazione

Il sistema è semi-automatizzato per facilitare l'aggiunta di nuovi sensori.

### Script di Generazione: `helpers/generate_sensors.py`
Questo script Python è il "motore" del sistema. Quando viene eseguito, rigenera i file di configurazione YAML basandosi sulla lista `devices`.
- Aggiorna i sensori SQL.
- Aggiorna i sensori Template.
- Aggiorna i sensori binari per le batterie.

### Notifiche Persistenti
L'automazione in `automations/th_battery_alerts.yaml` monitora i sensori di batteria e genera una **Persistent Notification** nella UI di Home Assistant quando è necessario un intervento umano.

## 3. Manutenzione

Per aggiungere un nuovo sensore (es. `th5e`):
1. Aprire `helpers/generate_sensors.py`.
2. Aggiungere `{"id": "th5e", "area": "nome_stanza"}` alla lista `devices`.
3. Eseguire lo script (o attendere la generazione automatica se prevista).
4. Ricaricare le configurazioni Template e SQL in Home Assistant.

---
*Ultimo aggiornamento: 30 Maggio 2026*
