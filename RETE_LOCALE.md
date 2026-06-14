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

### Dispositivi IoT (Amazon Echo)
- **alexa-cucina**
  - **IP:** `192.168.0.90`
  - **MAC:** `68:f6:3b:c3:cb:7e`
- **alexa-camera**
  - **IP:** `192.168.0.89`
  - **MAC:** `68:f6:3b:99:6b:a3`

## Analisi Impatto Mesh su Alexa
L'integrazione del sistema Tenda Mesh5 e la gestione dei canali su OpenWrt hanno portato alla seguente configurazione ottimizzata:

1.  **Backhaul Ethernet:** La base in cucina collegata via cavo garantisce prestazioni elevate per l'area giorno.
2.  **Ottimizzazione alexa-camera:**
    *   **Stato:** Forzata sulla **5GHz** del router OpenWrt.
    *   **Configurazione:** Inserita in **Blacklist** sulla 2.4GHz del router e sul sistema Tenda Mesh.
    *   **Performance:** Bitrate rilevato ~**260 MBit/s** (VHT80), segnale **-65 dBm** (SNR 43). Questo garantisce una banda passante molto superiore alla 2.4GHz e una latenza ridotta.
3.  **Ottimizzazione alexa-cucina:**
    *   **Stato:** Agganciata alla base Tenda Mesh (cablata).
    *   **Configurazione:** Inserita in **Blacklist** su OpenWrt (sia 2.4GHz che 5GHz) per forzare il collegamento al sistema Mesh locale e prevenire instabilità dovute a "missing ACKs".
4.  **Interferenza Canali:** Il router OpenWrt utilizza il **canale 149 (5GHz)** in modalità **VHT80** (fisso), mentre il Tenda Mesh opera sui canali bassi (es. 40), eliminando le sovrapposizioni.

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
*Ultimo aggiornamento: 1 Giugno 2026*
