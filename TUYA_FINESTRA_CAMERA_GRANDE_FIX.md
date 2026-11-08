# Fix: binary_sensor.finestra_camera_grande_finestra_camera_grande non disponibile

**Data:** 2026-11-07  
**Dispositivo:** Finestra camera grande (Tuya Contact Sensor)  
**Device ID:** `bf286f5f852a086ae6wltl`  
**MAC:** `20:f1:b2:94:5d:de`  
**IP:** `192.168.0.165`  
**Local Key:** `!i>eaLNT0Y(LHRYx`

---

## Sintesi del problema

L'entità `binary_sensor.finestra_camera_grande_finestra_camera_grande` risultava `unavailable` in Home Assistant nonostante:
- Il sensore fosse online su SmartLife (cloud)
- Il firewall (nftables) permettesse il traffico cloud per i dispositivi battery
- L'IP `.165` e MAC `20:f1:b2:94:5d:de` fossero corretti (confermati da ARP router)

---

## Causa radice

**LocalTuya tratta i dispositivi con `device_sleep_time > 0` come "cloud-only".**

Nel codice (`coordinator.py` righe 167-179, 206-213; `__init__.py` righe 375-382):
- Se `device_sleep_time > 0` → **connessione locale saltata** con messaggio: *"Device is cloud-only … skipping local connection, will use cloud polling"*
- I dati arrivano **solo da Tuya cloud** tramite due percorsi:
  1. Al riavvio HA: `_poll_cloud_devices_on_startup`
  2. Quando il network watcher rileva attività: `async_handle_network_event`
- Entrambi i percorsi richiedono `cloud_polling_enabled: true` (default)

**Configurazione errata applicata in precedenza:**
```json
"cloud_polling_enabled": false,   // ← DISABILITAVA l'unica fonte dati
"device_sleep_time": 60           // ← FORZAVA modalità cloud-only
```
Risultato: **nessuna fonte dati** → entità `unavailable` senza log di errore.

Il sensore cucina (`contact_cucina`, `bf2e5e78cb1bb32ac5ikh5`) funzionava perché aveva `cloud_polling_enabled` non impostato (default `true`).

---

## Soluzione applicata

### 1. Firewall (già corretto)
`helpers/tuya_selective_isolation.py` → proprietà `is_battery_sensor` estesa per rilevare sensori contatto/finestra/porta:
```python
@property
def is_battery_sensor(self) -> bool:
    text = f"{self.name} {self.model}".lower()
    return (
        self.name.lower().startswith("th")
        or "t&h" in text
        or "temperature & humidity" in text
        or "contact" in text
        or "door" in text
        or "window" in text
        or "finestra" in text
        or "porta" in text
    )
```
Risultato: `192.168.0.165` e `192.168.0.160` in `battery_ips` nftables → traffico cloud (DNS, NTP, Tuya TLS) permesso.

### 2. Configurazione LocalTuya (core.config_entries)
```json
{
  "device_id": "bf286f5f852a086ae6wltl",
  "protocol_version": "3.4",
  "device_sleep_time": 60,
  "cloud_polling_enabled": true,          // ← ESSENZIALE: abilita polling cloud
  "manual_dps_strings": "1,2,101,102",
  "dps_strings": [
    "1 ( code: contact , value: True )",
    "2 ( value: -1 )",
    "101 ( value: -1 )",
    "102 ( value: -1 )"
  ],
  "entities": [
    {"device_class": "door", "friendly_name": "finestra_camera_grande", "id": 1, "platform": "binary_sensor"},
    {"entity_category": "config", "friendly_name": "battery 2", "id": "2", "platform": "number", ...},
    {"entity_category": "config", "friendly_name": "not used", "id": "101", "platform": "number", ...},
    {"entity_category": "config", "friendly_name": "battery 102", "id": "102", "platform": "number", ...}
  ],
  "host": "192.168.0.165",
  "local_key": "!i>eaLNT0Y(LHRYx",
  "mac": "20:f1:b2:94:5d:de",
  "enable_debug": true
}
```

### 3. Pulizia entity registry
Rimosse entità stale (create 2026-10-28) per forzare ricreazione da config corretta:
```bash
# Filtro: config_entry_id=b5060bb88a434da4183e79c484b88142 AND device_id=finestra_camera_grande_device
```

---

## Verifica funzionamento

**Log attesi al riavvio HA:**
```
INFO  Polling Tuya Cloud for cloud-only device states on startup...
INFO  Found 5 cloud-only device(s) to poll: ..., bf286f5f852a086ae6wltl, ...
INFO  Querying cloud state for cloud-only device: bf286f5f852a086ae6wltl
INFO  Startup cloud polling completed for cloud-only devices
```

**Dopo trigger fisico (apri/chiudi finestra):**
```
INFO  Network activity detected for bf286f5f852a086ae6wltl, scheduling cloud poll
```

**Stato entità:**
```bash
ha_get_state binary_sensor.finestra_camera_grande_finestra_camera_grande
# {"state": "off", "attributes": {"device_class": "door", ...}}
```

---

## Note importanti

| Aspetto | Dettaglio |
|---------|-----------|
| **Modalità dati** | Cloud polling (non LAN) — latenza ~secondi, dipende da Tuya cloud |
| **Battery life** | Invariata: sensore si sveglia solo per eventi, cloud polling passivo |
| **MAC duplicato** | Risolto: cucina ha `bc:35:1e:ff:4a:b9`, camera grande `20:f1:b2:94:5d:de` |
| **DHCP statico** | Da configurare su router per fissare IP `.160` e `.165` ai rispettivi MAC |
| **enable_debug** | Impostato `true` per troubleshooting; rimuovere in produzione |

---

## Rollback (se necessario)

```bash
# 1. Ferma HA
docker stop homeassistant

# 2. Ripristina cloud_polling_enabled: false (o rimuovi chiave)
#    In core.config_entries per bf286f5f852a086ae6wltl

# 3. Pulisci entity registry per questo device
python3 -c "
import json
with open('.storage/core.entity_registry') as f: d=json.load(f)
d['data']['entities'] = [e for e in d['data']['entities'] 
    if not (e.get('config_entry_id')=='b5060bb88a434da4183e79c484b88142' 
            and e.get('device_id')=='finestra_camera_grande_device')]
with open('.storage/core.entity_registry', 'w') as f: json.dump(d, f)
"

# 4. Riavvia HA
docker start homeassistant
```

---

## File modificati

| File | Modifica |
|------|----------|
| `helpers/tuya_selective_isolation.py` | `is_battery_sensor` esteso per contact/door/window/finestra/porta |
| `.storage/core.config_entries` | `cloud_polling_enabled: true`, `protocol_version: "3.4"`, local DPs, entità DP 1 |
| `.storage/core.entity_registry` | Pulizia entità stale (ricreate al riavvio) |

---

## Comandi utili per troubleshooting futuro

```bash
# Verifica cloud-only devices registrati
grep "Registered cloud-only device" home-assistant.log

# Verifica polling cloud startup
grep "Polling Tuya Cloud for cloud-only" home-assistant.log

# Verifica network watcher trigger
grep "Network activity detected" home-assistant.log

# Verifica device reachable (ARP)
ip neigh show 192.168.0.165
ssh root@192.168.0.11 "ip neigh show 192.168.0.165"

# Verifica nftables battery_ips
ssh root@192.168.0.11 "nft list set inet tuya_block battery_ips"

# Stato entità
ha_get_state binary_sensor.finestra_camera_grande_finestra_camera_grande
```