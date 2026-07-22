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
