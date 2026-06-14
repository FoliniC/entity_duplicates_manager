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

## Conclusione Preliminare
La simulazione locale dell'handshake cloud richiede un server che agisca da proxy TLS trasparente o un'emulazione completa dei servizi MQTT/HTTPS di Tuya. Al momento, la soluzione più efficace per i sensori a batteria è consentire l'accesso WAN limitato ai soli domini Tuya necessari per l'attivazione.

## 6. Aggiornamento Operativo - 13 Giugno 2026

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
