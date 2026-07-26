# Architettura della Rete Locale

Documentazione della configurazione di rete per l'ambiente Home Assistant.

## Dispositivi Principali

### Server Home Assistant (Host)
- **Sistema Operativo:** Debian 13
- **Indirizzo IP:** `192.168.0.3`
- **Servizi:**
  - **Home Assistant:** Core della domotica.
  - **AdGuard Home:** Gestione DNS e DHCP per l'intera rete.

### Router (Gateway & Internet)
- **Hardware:** TP-Link AC1750 C7
- **Firmware:** OpenWrt 24.10 (LuCI)
- **Indirizzo IP:** `192.168.0.11`
- **Accesso:** SSH abilitato.
- **Funzione:** Accesso a Internet e routing locale.

### Desktop
- **Sistema Operativo:** Windows 11
- **Indirizzo IP:** `192.168.0.8`
- **Uso:** Workstation principale.

### Sistema Wi-Fi Mesh
- **Hardware:** Tenda AC1200 Mesh5 (MW5)
- **Configurazione:**
  - **Base (Cucina):**
    - **IP:** `192.168.0.10`
    - **Firmware:** `V1.0.0.33(6048)`
    - **MAC LAN:** `CC:2D:21:27:28:68` (Collegata via Ethernet al router)
    - **MAC WAN:** `CC:2D:21:27:28:6F`
    - **MAC Wi-Fi 2.4GHz:** `CC:2D:21:27:28:69`
    - **MAC Wi-Fi 5GHz:** `CC:2D:21:27:28:6C`
  - **Satellite 1 (Camera):** Collegamento mesh wireless.
  - **Satellite 2 (Balcone):** Collegamento mesh wireless.
- **Funzione:** Estensione della copertura Wi-Fi per aree non raggiunte direttamente dal router.
- **Canale 2.4GHz:** Fisso su **Canale 1** (evita roaming che destabilizza i dispositivi Tuya IoT). Vedi [`tuya_handshake.md`](./tuya_handshake.md#6-ottimizzazione-wi-fi-e-roaming-prevenzione-wake-up-failed-e-heartbeat-timeout) per heartbeat timeout e gestione canali.

### Dispositivi IoT (Amazon Echo)
- **alexa-cucina**
  - **IP:** `192.168.0.90`
  - **MAC:** `68:f6:3b:c3:cb:7e`
- **alexa-camera**
  - **IP:** `192.168.0.89`
  - **MAC:** `68:f6:3b:99:6b:a3`

## Analisi Impatto Mesh e Ottimizzazione Canali (Alexa & Tuya)
L'integrazione del sistema Tenda Mesh5 e la gestione dei canali su OpenWrt hanno portato alla seguente configurazione ottimizzata:

1.  **Backhaul Ethernet:** La base in cucina collegata via cavo garantisce prestazioni elevate per l'area giorno.
2.  **Ottimizzazione alexa-camera:**
    *   **Stato:** Forzata sulla **5GHz** del router OpenWrt.
    *   **Configurazione:** Inserita in **Blacklist** sulla 2.4GHz del router e sul sistema Tenda Mesh.
    *   **Performance:** Bitrate rilevato ~**260 MBit/s** (VHT80), segnale **-65 dBm** (SNR 43). Questo garantisce una banda passante molto superiore alla 2.4GHz e una latenza ridotta.
3.  **Ottimizzazione alexa-cucina:**
    *   **Stato:** Agganciata alla base Tenda Mesh (cablata).
    *   **Configurazione:** Inserita in **Blacklist** su OpenWrt (sia 2.4GHz che 5GHz) per forzare il collegamento al sistema Mesh locale e prevenire instabilità dovute a "missing ACKs".
4.  **Interferenza Canali 5GHz:** Il router OpenWrt utilizza il **canale 149 (5GHz)** in modalità **VHT80** (fisso), mentre il Tenda Mesh opera sui canali bassi (es. 40), eliminando le sovrapposizioni.
5.  **Interferenza Canali 2.4GHz & Stabilità Tuya:**
    *   **Configurazione:** Il router OpenWrt è impostato sul **Canale 1 (2.4GHz)** fisso, mentre il sistema Tenda Mesh è impostato sul **Canale 11 (2.4GHz)** fisso per eliminare le sovrapposizioni di banda 2.4GHz.
    *   **Mitigazione Roaming Tuya:** Il MAC address di `luci-cucina` (`50:8b:b9:44:d0:bb`, IP `192.168.0.66`) non e' piu' in blacklist sulla 2.4GHz del router OpenWrt. Il dispositivo puo' quindi associarsi anche all'AP OpenWrt; l'accesso WAN resta limitato dalle regole Tuya selettive. Maggiori dettagli in [tuya_handshake.md](file:///home/carlo/docker/homeassistant/config/tuya_handshake.md#L45-L60).

## Note di Configurazione
- Il server Debian (`192.168.0.3`) funge da centro di controllo sia per la domotica che per i servizi di rete critici (DNS/DHCP tramite AdGuard).
- L'accesso al router OpenWrt è possibile via Web UI (LuCI) o terminale (SSH).

## Monitoraggio del Traffico di Rete

Per diagnosticare rallentamenti e identificare dispositivi che saturano la banda, è stato implementato un sistema di monitoraggio integrato.

### Componenti del Sistema
1.  **Router (Data Source):**
    *   **Servizio:** `nlbwmon` installato sul TP-Link Archer C7.
    *   **Funzione:** Tiene traccia del traffico (byte/pacchetti) per ogni MAC/IP della rete.
    *   **Accesso:** SSH abilitato con chiave dedicata in `/config/.ssh/router_key`.
    *   **Configurazione Ottimizzata (Giugno 2026):**
        - **Commit Interval:** Impostato a `1m` (in RAM) per avere dati quasi real-time.
        - **Flow Offloading:** Disattivato (`flow_offloading='0'`, `flow_offloading_hw='0'`). Questa modifica è necessaria perché l'offloading accelera il traffico bypassando i contatori della CPU, rendendo invisibile il traffico dei dispositivi collegati tramite bridge/mesh (es. Alexa in cucina).
2.  **Server HA (Integrazione Avanzata):**
    *   **Monitoraggio Qualità (Livello 1):** `helpers/network_quality.py` (ogni 60s). Misura **Packet Loss**, **Jitter** e **Latenza** tramite ping sequenziali.
    *   **Watchdog Tunnel Cloudflare (Livello 1.5):** `packages/cloudflare_watchdog.yaml`. Controlla ogni 60s la raggiungibilità dell'URL esterno (`https://home.vialeformica.org`). Se l'URL non risponde per oltre **5 minuti**, il sistema esegue automaticamente il riavvio del container `cloudflare-tunnel` tramite SSH sul server host.
        - **Container atteso:** `cloudflare-tunnel` sul server Docker `192.168.0.3`.
        - **Comandi HA:** `yaml_generator/shell_command/cloudflare.yaml` esegue `docker start|stop|restart cloudflare-tunnel` via SSH usando `/config/.ssh/host_key`.
        - **Ricreazione se il container viene perso:** recuperare il token da Cloudflare Dashboard -> Zero Trust -> Networks -> Tunnels, oppure dal link diretto `https://dash.cloudflare.com/929828bf22cac620ccecfb4f126da3de/tunnels`. Selezionare il tunnel di `home.vialeformica.org` -> Overview -> Add a replica. Copiare il comando `cloudflared tunnel run --token ...` e usare solo il token.
        - **Comando Docker di ripristino:**
          ```bash
          docker run -d \
            --name cloudflare-tunnel \
            --restart unless-stopped \
            --network host \
            cloudflare/cloudflared:latest \
            tunnel --no-autoupdate run --token '<TOKEN_DA_CLOUDFLARE>'
          ```
        - **Verifica:** `docker logs --tail 120 cloudflare-tunnel` deve mostrare `Registered tunnel connection` e la config remota `home.vialeformica.org -> http://192.168.0.3:8123`. Da Home Assistant, `curl -I https://home.vialeformica.org` deve restituire `HTTP/2 200`.
        - **Nota backup:** il backup Home Assistant contiene watchdog e shell command, ma non contiene i container Docker. Il backup GitHub genera una copia sanitizzata del compose host in `host_backup/docker-compose.yml`.
    *   **Velocità WAN (Livello 2):** `helpers/wan_traffic_realtime.py` (ogni 10s). Legge `/proc/net/dev` per la banda totale istantanea e calcola la **Saturazione %**.
    *   **Real-time Per-Device (Livello 3):** `helpers/realtime_per_device.py` (ogni 15s). Utilizza **nftables accounting** sul router per tracciare la banda dei dispositivi critici (Desktop, Alexa, HA).
    *   **Diagnosi Automatica:** Package `packages/network_diagnosis.yaml`. Un sensore template (`sensor.network_status_diagnosis`) incrocia i dati dei tre livelli per identificarle se eventuali rallentamenti sono causati dalla linea o dalla saturazione locale.
    *   **Boost Mode:** Sistema per aumentare temporaneamente la frequenza di campionamento tramite `input_boolean.network_boost_mode`. La durata e l'intervallo (2-15s) sono configurabili dall'utente.
        - *Nota tecnica:* Grazie all'implementazione di **SSH Multiplexing (ControlMaster)**, la sessione rimane aperta per tutta la durata del boost. Questo azzera l'overhead di connessione/autenticazione, rendendo l'intervallo di 2s estremamente leggero per la CPU del router.

3.  **Dashboard di Controllo:**
    *   **Visualizzazione:** Dashboard "Traffico internet" a due colonne.
    *   **Funzionalità:**
        - **Colonna Sinistra:** Diagnosi automatica, indicatori di qualità (Loss/Jitter), saturazione e riepilogo storico (nlbwmon).
        - **Colonna Destra:** Andamento real-time grafico e tabella "Chi sta usando banda ORA?" (dati nftables).
        - **Interattività:** Tutte le card supportano la selezione del testo per l'esportazione manuale dei dati.

### Configurazione Grafico Top 5 Dispositivi
...
---
*Ultimo aggiornamento: 10 Giugno 2026*
1.  **Sensori Template** (`/config/packages/network_monitoring.yaml`): Sono definiti 5 sensori individuali (`top_device_1_mb` ... `top_device_5_mb`). 
    - **Nome statico**: "Top Device X MB" per un'identificazione univoca nel database.
    - **Stato**: Valore numerico del traffico (MB).
    - **Attributo `device_name`**: Contiene il nome dinamico del dispositivo.

2.  **ApexCharts Card** (`/config/dashboards/internet_traffic.yaml`): Visualizza i 5 sensori come serie individuali in modalità minimale.
    ```yaml
    series:
      - entity: sensor.top_device_1_mb
      - entity: sensor.top_device_2_mb
      - entity: sensor.top_device_3_mb
      - entity: sensor.top_device_4_mb
      - entity: sensor.top_device_5_mb
    ```

3.  **Vantaggi:** 
    - **Massima Compatibilità**: Non usa script JavaScript né template nella card, rendendola immune a problemi di timing o versioning del frontend.
    - **Stabilità dei Dati**: I sensori hanno stati numerici standard, ideali per la gestione dello storico di HA.

---
*Ultimo aggiornamento: 25 Luglio 2026*

## Collegamento SSH tra Server

Il server Debian (192.168.0.3) funge da pivot per la gestione remota degli altri dispositivi di rete tramite SSH. Le chiavi sono nel container HA (`/config/.ssh/`) e montate anche sul filesystem host (`/home/carlo/docker/homeassistant/config/.ssh/`).

### Chiavi SSH disponibili

| Chiave | Formato | Utilizzo | Host |
|---|---|---|---|
| `host_key` | RSA 4096 | Loopback locale (Debian) | `carlo@localhost` (via sudo) |
| `router_key` | (inherited) | Router OpenWrt | `root@192.168.0.11` |
| `win_key` | ED25519 | PC Windows 11 | `carlo_2@192.168.0.8` |

### Comandi di collegamento

**Router OpenWrt (192.168.0.11):**
```bash
ssh -i /config/.ssh/router_key -o StrictHostKeyChecking=no root@192.168.0.11
```

**Server Debian locale (loopback):**
```bash
ssh -i /config/.ssh/host_key -o StrictHostKeyChecking=no carlo@localhost
```

**PC Windows 11 (192.168.0.8):**
```bash
ssh -i /config/.ssh/win_key -o StrictHostKeyChecking=no carlo_2@192.168.0.8
```

### Script di tethering USB

Entrambi i server host supportano lo script di tethering USB:

| Server | Script | Path remoto |
|---|---|---|
| Debian (192.168.0.3) | `usb_tether.sh` (bash) | `/home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh` |
| Windows (192.168.0.8) | `usb_tether.ps1` (PowerShell) | `C:\Scripts\usb_tether.ps1` |

**Esecuzione da remoto (Windows):**
```bash
ssh -i /config/.ssh/win_key carlo_2@192.168.0.8 \
  "powershell -ExecutionPolicy Bypass -File C:\Scripts\usb_tether.ps1 -Action status"
```

### Note di sicurezza
- Le chiavi sono NON password-protette (uso automation).
- Il file `host_key` è usato anche per il ControlMaster SSH Multiplexing.
- `win_key` è stata generata appositamente per Windows (formato ED25519, più compatibile con OpenSSH for Windows 9.5).
- Il router accetta solo connessioni SSH chiave, password disabilitata.
