# Analisi Handshake e Comunicazione Dispositivi Tuya

Questa documentazione riassume le informazioni raccolte durante l'analisi del traffico dei dispositivi Tuya (alimentati e a batteria) in seguito all'isolamento internet.

## 1. Architettura della Comunicazione
I dispositivi Tuya utilizzano un modello di comunicazione ibrido:
- **Locale (Porta 6668/TCP)**: Utilizzata da LocalTuya/Tuya Local per il controllo e la ricezione degli stati.
- **Cloud (Porte 8883, 8886, 443/TCP)**: Utilizzata per l'handshake iniziale, la sincronizzazione dell'orario e la validazione della sessione.
- **Discovery (Porta 6667/UDP)**: I dispositivi inviano pacchetti broadcast UDP per annunciare la loro presenza sulla rete locale.

## 2. Comportamento Post-Isolamento
L'isolamento WAN ha evidenziato due comportamenti distinti:

### Dispositivi Alimentati (es. Luci, Smart Meter)
- Rimangono connessi al WiFi anche senza accesso WAN.
- Continuano a inviare broadcast UDP sulla porta 6667.
- Tentano continuamente di stabilire connessioni TCP verso il cloud (es. `63.178.174.95:8883` o `18.184.31.90:8886`).
- Funzionano correttamente con LocalTuya perché il server locale rimane attivo.

### Dispositivi a Batteria (es. Sensori TH3C, TH2B)
- Sono "sleepy devices": si svegliano solo per inviare dati.
- **Senza internet**: Se l'handshake cloud fallisce (timeout o rifiuto), il dispositivo **spegne immediatamente il modulo WiFi** per preservare la batteria.
- **Risultato**: Diventano invisibili in rete (non rispondono al ping, nessun ARP entry) e non possono essere letti localmente.

## 3. Analisi del Traffico Cloud Intercettato
Dalle catture effettuate (es. `192.168.0.66` e `192.168.0.47`):
- **DNS**: I dispositivi cercano domini come `m2.tuyaeu.com`, `openapi.tuyaeu.com`, `m3-eu.lifeaiot.com`.
- **TLS Handshake**: La comunicazione inizia con un pacchetto `Client Hello` (TLS 1.2/1.3).
    - Esempio hex intercettato: `16 03 03 00 4a 01 00 00 46 03 03 ...`
- **Crittografia**: Tuya utilizza crittografia AES per i dati e TLS per il trasporto cloud. L'handshake include lo scambio di certificati e chiavi effimere, rendendo il "Man-in-the-Middle" (MITM) estremamente complesso senza l'installazione di un certificato CA nel firmware del dispositivo (impossibile su Tuya standard).

## 4. Sfide per la Simulazione (Mocking)
Simulare la risposta cloud locale è difficile per i seguenti motivi:
1. **Validazione Certificati**: I dispositivi verificano l'identità del server Tuya tramite certificati SSL. Un server locale verrebbe rifiutato a meno di non emulare l'intera infrastruttura PKI di Tuya.
2. **Timing**: I sensori a batteria rimangono accesi per pochissimi secondi. La risposta deve essere istantanea.
3. **Firmware Moderno**: Molte versioni recenti del firmware Tuya richiedono una connessione persistente o periodica al cloud per mantenere abilitata la porta locale 6668.

## 5. Stato Dispositivi Analizzati
| IP | Nome | Tipo | Stato Isolato | Note |
|---|---|---|---|---|
| 192.168.0.41 | TH3C | Batteria | Offline | Scomparso dalla rete |
| 192.168.0.66 | Luci cucina | Alimentato | Online | Funziona LocalTuya |
| 192.168.0.47 | Garage | Alimentato | Online | Handshake cloud fallito ma WiFi attivo |

## 6. Ottimizzazione Wi-Fi e Roaming (Prevenzione "Wake-up failed" e "Heartbeat timeout")
Per i dispositivi Tuya alimentati (es. `luci-cucina` ad IP `192.168.0.66`) e a batteria, un problema ricorrente è il continuo "roaming" (saltellamento) tra l'Access Point principale (OpenWrt) e i satelliti Mesh (Tenda MW5), oppure la perdita di connessione dovuta a segnale debole/interferenza. Questo comportamento innesca i log di errore "Wake-up failed", "invalid key size for AES" e **"Heartbeat failed due to timeout"**, evidenziato dai log LocalTuya:

```
[Luci cucina] Reconnect succeeded on attempt: 3
[Luci cucina] Heartbeat failed due to timeout, disconnecting
[Luci cucina] Disconnected due to: Connection lost
```

### Cause Identificate
1. **Heartbeat timeout ricorrenti** (19:00:39 → 19:00:44 → 19:01:04): Il dispositivo perde pacchetti verso il Tenda Mesh, non risponde al keepalive di LocalTuya e viene disconnesso. Si riconnette dopo 10-20 secondi. Questo ciclo si ripete all'infinito, causando:
   - Spegnimenti/accesioni fantasma della luce (ogni riconnessione può ri-sincronizzare i DPS)
   - Log di sistema saturi di tentativi di riconnessione
   - Instabilità generale del controllo luci
2. **Segnale WiFi debole**: Il dispositivo potrebbe essere al limite della copertura del Tenda Mesh (specialmente se il satellite è più lontano della base).
3. **Interferenza canale 1**: Il Tenda Mesh è configurato su canale 1 (2.4GHz). Se ci sono reti vicine sullo stesso canale, l'interferenza causa pacchetti persi.

### Contromisure Adottate
1. **Spostamento e Fissaggio dei Canali 2.4GHz**:
   - **Router OpenWrt**: **Canale 149 (5GHz)** configurato - **NESSUN SSID 2.4GHz**. I dispositivi Tuya, operanti solo a 2.4GHz, non possono connettersi al router.
   - **Tenda Mesh**: Configurato fisso sul **Canale 1** (2.4GHz).
   - *Motivazione*: Forzando tutti i dispositivi Tuya 2.4GHz sul solo Tenda Mesh (canale 1), si elimina la possibilità di roaming spurio verso il router. Ma se il canale 1 è congestionato, il problema heartbeat persiste.

2. **Forzatura del Collegamento (BSSID Binding / MAC Blacklisting)**:
   - Il MAC del dispositivo `luci-cucina` (`50:8b:b9:44:d0:bb`, IP `192.168.0.66`) e' stato rimosso dalla **Blacklist 2.4GHz** del router OpenWrt. Il dispositivo puo' tentare l'associazione anche all'AP OpenWrt.
   - La blacklist OpenWrt resta disponibile solo come contromisura da riapplicare se il roaming dovesse causare nuovamente heartbeat timeout.

3. **Heartbeat keepalive persistente**: Il modulo LocalTuya riprova automaticamente la connessione. **Non è una soluzione**, ma contiene il danno.

### Contromisure da Valutare
Se il problema heartbeat persiste nonostante i punti precedenti:

1. **Cambiare canale 2.4GHz del Tenda Mesh (canale 6 o 11)**:
   - Aprire l'app Tenda → Impostazioni Wi-Fi → 2.4GHz → Canale → Selezionare **6** o **11** (non automatico)
   - *Perché*: Se il canale 1 è affollato (reti vicine, baby monitor, ecc.), lo spostamento riduce l'interferenza e stabilizza il segnale.
2. **Aggiungere un AP 2.4GHz dedicato per IoT**:
   - Un router secondario o un ESPHome in modalità AP, posizionato vicino al device problematico, con un SSID separato ("IoT_2G").
3. **Abbassare la soglia di potenza del Tenda** per evitare che il satellite si connetta alla base da troppo lontano con segnale debole.
4. **Verificare con app WiFi Analyzer** (da uno smartphone) la congestione del canale 1 nell'area cucina.

### Log Utili
```bash
# Da HA: heartbeat timeout e riconnessioni
tail -f /config/home-assistant.log | grep "Luci cucina"

# Dal router OpenWrt: autenticazioni WiFi fallite
ssh root@192.168.0.11 "logread -f" | grep "did not acknowledge"
```

## 7. Conclusioni Finali e Raccomandazioni (15 Giugno 2026)

L'analisi approfondita del comportamento dei sensori Tuya a batteria (serie TH) ha portato alle seguenti conclusioni definitive:

1.  **Handshake Cloud Mandatorio**: I sensori a batteria **non abilitano la porta locale 6668** (necessaria per LocalTuya) se non riescono a completare con successo l'handshake TLS con il cloud Tuya ad ogni risveglio.
2.  **Comportamento in caso di Blocco**: Se il cloud è irraggiungibile (blocco WAN totale):
    *   Il sensore tenta la connessione cloud per alcuni secondi.
    *   In assenza di risposta, **spegne immediatamente il modulo WiFi** per risparmiare batteria.
    *   Il dispositivo risulta `FAILED` o `INCOMPLETE` nelle tabelle ARP/Neighbor del router e non risponde a nessuna sollecitazione locale (ping o tentativi di connessione LocalTuya).
3.  **LocalTuya Shadow Fallback**: Quando il sensore si sveglia e ha accesso al cloud, ma la connessione locale fallisce o è instabile, LocalTuya utilizza il "Cloud shadow fallback". Questo messaggio indica che i dati vengono letti via Internet dai server Tuya invece che direttamente via LAN.

### 💡 Consigli Operativi per l'Isolamento
Per i sensori a batteria, l'isolamento totale **non è praticabile**. La strategia consigliata è l'**accesso WAN selettivo**:

*   **DNS**: Consentire richieste DNS verso i domini Tuya (es. `*.tuyaeu.com`, `*.lifeaiot.com`).
*   **Handshake Ports**: Aprire le porte TCP `443`, `8883` e `8886` verso gli IP del cloud Tuya.
*   **NTP**: Consentire il traffico UDP sulla porta `123` (fondamentale per la validazione dei certificati TLS).
*   **Script di Automazione**: Utilizzare lo script `helpers/tuya_selective_isolation.py` per aggiornare dinamicamente le regole del firewall in base agli IP cloud risolti, minimizzando l'esposizione WAN.

Se i sensori non aggiornano i valori dopo aver ripristinato la connettività, è necessario attendere un **evento fisico** (cambio temperatura/umidità) o premere il tasto di reset/wake-up sul dispositivo per forzare una nuova associazione WiFi.

### Diagnosi sul Router
La tabella `inet tuya_block` su OpenWrt blocca i dispositivi Tuya tramite il set `blocked_ips`. Il blocco pieno intercetta anche le richieste DNS redirette verso AdGuard (`192.168.0.3`), quindi una allowlist basata sui domini Tuya non puo' funzionare se prima non si consente ai sensori di risolvere quei domini.

Sensori TH a batteria rilevati in LocalTuya:
| IP | Nome LocalTuya | Stato Policy | Stato ARP Router |
|---|---|---|---|
| `192.168.0.40` | th2b temperature humidity | Bloccato con allowlist selettiva | `STALE` |
| `192.168.0.41` | th3c temperature humidity | Bloccato con allowlist selettiva | `FAILED` |
| `192.168.0.42` | th4d temperature humidity | Bloccato con allowlist selettiva | `STALE` |
| `192.168.0.139` | th1a temperature humidity | Bloccato con allowlist selettiva | `STALE` |

Prima della correzione, solo `192.168.0.41` aveva una regola `accept` completa; gli altri TH erano ancora nel blocco pieno. La regola `accept` completa del TH3C e' stata rimossa con `apply --strict-battery`, quindi anche `192.168.0.41` ora usa solo l'accesso minimo selettivo.

### Soluzione Implementata
Sono stati aggiunti:
- `helpers/tuya_selective_isolation.py`
- `packages/tuya_selective_isolation.yaml`

Lo script:
- legge i device da `.storage/core.config_entries`;
- individua i sensori TH a batteria;
- risolve i domini Tuya tramite AdGuard;
- mantiene una cache locale bounded degli IP cloud Tuya visti nelle ultime 24 ore (`temp/tuya_selective_isolation_cloud_ips.json`);
- aggiorna i set nftables `battery_ips` e `allowed_tuya_cloud`;
- reinstalla regole nftables marcate `tuya-selective-*`, eliminando eventuali duplicati precedenti.

Il package Home Assistant richiama:
```bash
python3 /config/helpers/tuya_selective_isolation.py apply --strict-battery
```

all'avvio di Home Assistant e ogni 10 minuti, per assorbire il DNS round-robin dei domini Tuya senza aprire intere reti cloud.

### Regole nftables Attive
Le regole selettive sono posizionate prima del drop su `@blocked_ips`:
```text
ip saddr @battery_ips ip daddr 192.168.0.3 udp dport 53 accept comment "tuya-selective-dns-udp"
ip saddr @battery_ips ip daddr 192.168.0.3 tcp dport 53 accept comment "tuya-selective-dns-tcp"
ip saddr @battery_ips ip daddr @allowed_tuya_cloud tcp dport { 443, 8883, 8886 } accept comment "tuya-selective-cloud"
ip saddr @battery_ips udp dport 123 accept comment "tuya-selective-ntp"
ip saddr @blocked_ips drop
```

Il set `battery_ips` contiene:
```text
192.168.0.40, 192.168.0.41, 192.168.0.42, 192.168.0.139
```

Domini Tuya monitorati:
- `m2.tuyaeu.com`
- `openapi.tuyaeu.com`
- `m3-eu.lifeaiot.com`

Porte consentite per il cloud Tuya:
- TCP `443`
- TCP `8883`
- TCP `8886`

Traffico aggiuntivo consentito:
- DNS verso AdGuard `192.168.0.3:53` su UDP/TCP
- NTP UDP/123

Tutto il resto resta soggetto al blocco esistente tramite `blocked_ips`.

### Comandi Utili
```bash
venv/bin/python helpers/tuya_selective_isolation.py status
venv/bin/python helpers/tuya_selective_isolation.py apply --strict-battery
venv/bin/python helpers/tuya_selective_isolation.py remove --flush-sets
```

### Stato e Limiti
- `192.168.0.41` (`sensor.th3c_temperature`) risulta ancora `FAILED` in ARP: il sensore e' probabilmente gia' in sleep e la policy non puo' svegliarlo.
- La correzione avra' effetto al prossimo wake-up/riassociazione Wi-Fi del sensore.
- Se dopo il prossimo wake-up il TH3C resta indisponibile, la prossima verifica utile e' una cattura del traffico durante il risveglio per scoprire eventuali altri domini Tuya da aggiungere alla lista.
- La strategia MITM/mock del cloud resta sconsigliata: TLS, validazione certificati e tempi di wake-up dei sensori rendono la soluzione fragile rispetto a una allowlist WAN minima.

---

## Expected Behavior of "Aggiungi Nuovo Dispositivo" (Manual Cloud Import)

The "aggiungi nuovo dispositivo" (add new device) flow in LocalTuya follows this sequence:

1. **Cloud API attempt** — LocalTuya tries to contact the Tuya Cloud API to fetch the device list.
2. **If cloud fails** (authorization error, network issue, etc.):
   - **No cache exists** → the user is shown a form to paste the raw Tuya Cloud JSON manually.
   - **Cache exists** → the user is shown a 3-option selector:
     - `📂 Use cached device list` — use the previously cached JSON as-is, skip re-fetching.
     - `🔄 Fetch fresh from Tuya Cloud` — re-fetch the device list from Tuya Cloud, update the cache,
       filter out already-configured devices, and proceed.
     - `📝 Paste new JSON` — paste a new JSON payload from the Tuya Cloud API.
3. **Format 1 JSON parsed** (`{"result": {"data": [...]}}`) — the list of `res_id` device IDs is
   filtered to exclude already-configured devices (by cloud ID and MAC address). The remaining
   unconfigured device IDs are stored as `_manual_device_ids` and the user proceeds to step 2.
4. **Step 2: Format 2 JSON** — the user pastes detailed device info JSON
   (`{"result": [...]}` with full device objects including `id`, `local_key`, `ip`, `product_id`,
   `mac`, etc.). A pre-import duplicate check runs before merging into `cloud_data.device_list`:
   - Devices already configured by cloud ID → **skipped**
   - Devices with a MAC that matches an existing configured device → **skipped**
     (catches factory-reset devices that got new cloud IDs but keep the same hardware MAC)
   - If all devices are filtered → `all_devices_configured` error is shown.
   - Otherwise the filtered devices are merged and the individual device configuration form is shown.

## API Endpoint Verification

### Original hass-localtuya (xZetsubou / reference implementation)

| Purpose | Endpoint | HTTP Method |
|---|---|---|
| Authentication | `/v1.0/token?grant_type=1` | GET |
| Get all user devices | `/v1.0/users/{uid}/devices` | GET |
| Get device info | `/v1.0/devices/{device_id}` | GET |
| Get device functions | `/v1.0/devices/{device_id}/functions` | GET |
| Get device specs (fallback) | `/v1.1/devices/{device_id}/specifications` | GET |
| Get space resources | `/v2.0/cloud/space/{space_id}/resource` | GET |
| Get child spaces | `/v2.0/cloud/space/child` | GET |
| Get space info | `/v2.0/cloud/space/{space_id}` | GET |

### Modified Implementation (localtuya config_flow.py + tuya_gui.py + cloud_api.py)

| Purpose | Endpoint | HTTP Method | Where Used | Matches Original? |
|---|---|---|---|---|
| Authentication | `/v1.0/token?grant_type=1` | GET | `cloud_api.py:230` | ✅ Yes |
| Get all user devices | `/v1.0/users/{user_id}/devices` | GET | `cloud_api.py:259` | ✅ Yes |
| Get device info | `/v1.0/devices/{dev_id}` | GET | `tuya_gui.py:3835` | ✅ Yes |
| Get device specs fallback | `/v1.1/devices/{dev_id}/specifications` | GET | `tuya_gui.py:3845` | ✅ Yes |
| Get device functions | (via internal API) | GET | `cloud_api.py:async_get_device_functions` | ✅ Yes |
| Get space resources | `/v2.0/cloud/space/{space_id}/resource` | GET | `tuya_gui.py:4092`, `cloud_api.py:494` | ✅ Yes |
| Get child spaces | `/v2.0/cloud/space/child` | GET | `cloud_api.py:470` | ✅ Yes |
| Get space info | `/v2.0/cloud/space/{space_id}` | GET | tuya_gui.py (device details) | ✅ Yes |

### Endpoint Status Summary

All Tuya Cloud API endpoints used in the modified implementation match the original `hass-localtuya`
reference implementation exactly. No endpoints have been added, removed, or changed.

### LocalTuya Manual Import JSON Formats

**Format 1** (used in step 1 of manual cloud import):
```json
{
  "result": {
    "data": [
      {"res_id": "bfc0abab874dc1a864q5kn", "res_type": 0},
      {"res_id": "bf054a2177fd16678d9yds", "res_type": 0}
    ],
    "last_row_key": 2031162322342079,
    "page_size": 200
  },
  "success": true,
  "t": 1785229260540,
  "tid": "daa2e1a18a6211f19cb812e3d0098c67"
}
```

**Format 2** (used in step 2 of manual cloud import — detailed device info):
```json
{
  "result": [
    {
      "active_time": 1741388374,
      "bind_space_id": "150797786",
      "category": "tdq",
      "create_time": 1695142031,
      "custom_name": "",
      "icon": "smart/icon/ay1533257659316XGZOd/1f21cca41812827d145dc1620bf8a835.jpg",
      "id": "bfc0abab874dc1a864q5kn",
      "ip": "109.53.1.80",
      "is_online": false,
      "lat": "0",
      "local_key": "&t-ii)HEj{'W]PSq",
      "lon": "0",
      "model": "",
      "name": "1CH WiFi Switch Module 3",
      "product_id": "1o5lr0wtvu2bziz6",
      "product_name": "1CH WiFi Switch Module CB3S",
      "sub": false,
      "time_zone": "+01:00",
      "update_time": 1741388379,
      "uuid": "a1fe4be9b7581dbc"
    }
  ]
}
```

### Duplicate Detection (Three Layers)

1. **Layer 1 — unconfigured_devices filter (step 1, Format 1 path)**:
   - Excludes devices by cloud ID (`res_id`/`id`) AND MAC address
   - Only unconfigured devices pass through to step 2

2. **Layer 2 — pre-import check (step 2, Format 2 JSON path)**:
   - Before merging into `cloud_data.device_list`, each device from Format 2 JSON is checked:
     - Already-configured cloud ID → skipped
     - MAC match with any configured device → skipped (catches factory-reset devices with new cloud IDs)
   - If all devices filtered → `all_devices_configured` error shown

3. **Layer 3 — configure_device duplicate check**:
   - Per-device check during individual configuration
   - Matches by IP, cloud device ID, and MAC (including MAC from cloud data for factory-reset devices)
   - Shows `duplicate_device` error if conflict detected

---

## Update Cache Flow (Auto-fetch Detailed Device Info)

When the user selects `🔄 Fetch fresh from Tuya Cloud` in the manual cloud import dialog, the flow now implements a fully automated multi-step process:

### Step 1: Space Selection
- Calls `/v2.0/cloud/space/child` to fetch all spaces from Tuya Cloud
- Presents a dropdown for user to select a space

### Step 2: Fetch & Filter Devices
- Calls `/v2.0/cloud/space/{space_id}/resource` to get all devices in selected space
- Filters out already-configured devices by cloud device ID
- Logs: "total devices from space: X, unconfigured: Y, filtered out: Z"

### Step 3: Auto-fetch Detailed Device Info (NEW)
For each unconfigured device ID, automatically calls `/v1.0/devices/{device_id}` to fetch full device details:
- `local_key`, `ip`, `mac`, `uuid`, `product_id`, `product_name`, `category`, `model`, etc.
- Logs each device's details: name, MAC, IP

### Duplicate Detection in Detailed Info (NEW)
After fetching all device details, performs a comprehensive duplicate check against already-configured devices:
- **MAC address match** — catches factory-reset devices with new cloud IDs but same hardware MAC
- **IP address match** — catches devices sharing the same local IP
- **Cloud device ID match** — catches already-configured devices

Duplicates are logged with details:
```
Duplicate filtered: bfc0abab874dc1a864q5kn (MAC match with existing_dev: aa:bb:cc:dd:ee:ff)
Duplicate filtered: bf054a2177fd16678d9yds (IP match with existing_dev: 192.168.1.100)
```

Only unique devices proceed to the `configure_device` step.

### Step 4: Proceed to Configuration
- Merges unique devices into `cloud_data.device_list`
- Proceeds directly to `async_step_add_device()` for individual device configuration
- Skips the manual Format 2 JSON paste step entirely

### Logging
All API calls use the same `ListHandler` pattern as `tuya_gui.py`:
- Captures `cloud_api` debug logs via `ListHandler`
- Logs full request/response payloads with `[CLOUD-API]` prefix
- Logs duplicate detection results with device IDs and match reasons
- Format matches `tuya_gui.py` for side-by-side log comparison
