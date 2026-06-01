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

2.  **Server HA (Integrazione):**
    *   **Script:** `helpers/router_traffic.py`.
    *   **Logica:** Interroga il router ogni 60 secondi, calcola la velocità differenziale (kbps) e risolve i nomi host tramite DNS locale (`socket`).
    *   **Entità:** Gestite tramite il package `packages/network_monitoring.yaml`.
        - `sensor.router_total_download`: Traffico totale in ingresso (GB).
        - `sensor.router_total_upload`: Traffico totale in uscita (GB).
        - `sensor.router_traffic_stats`: Attributo `top_consumers` con la lista dettagliata dei device.

3.  **Dashboard di Controllo:**
    *   **Visualizzazione:** Dashboard dedicata "Traffico Rete".
    *   **Funzionalità:**
        - Tabella interattiva ordinabile (`flex-table-card`) con nomi amichevoli dei dispositivi.
        - Grafico a barre dei primi 10 consumatori per MB totali.
        - Grafico real-time della velocità complessiva (KB/s) nell'ultima ora.

### Configurazione Grafico Top 5 Dispositivi
Il grafico "Top 5 Dispositivi (MB)" utilizza una struttura a tre livelli per garantire prestazioni e stabilità:

1.  **Sensore Helper** (`/config/packages/network_monitoring.yaml`): Prepara i dati come un unico oggetto JSON pronto per il grafico.
    ```yaml
    - name: "Router Top 5 Chart Data"
      unique_id: router_top_5_chart_data
      state: "ok"
      attributes:
        chart_data: >-
          {% set top = state_attr('sensor.router_traffic_stats', 'top_consumers') %}
          {% if top %}
            {% set data = namespace(items=[]) %}
            {% for d in top[:5] %}
              {% set data.items = data.items + [{"x": d.name, "y": d.total_rx_mb}] %}
            {% endfor %}
            {{ data.items }}
          {% else %}
            []
          {% endif %}
    ```

2.  **ApexCharts Card** (`/config/dashboards/internet_traffic.yaml`): Visualizza i dati leggendo direttamente l'attributo pre-formattato.
    ```yaml
    series:
      - entity: sensor.router_top_5_chart_data
        ignore_history: true # Obbligatorio per bypassare la history API su sensori non numerici
        data_generator: |
          const raw = entity.attributes.chart_data;
          if (!raw) return [];
          const data = typeof raw === 'string' ? JSON.parse(raw) : raw;
          return data.map(d => [d.x, d.y]); # Formato array piatto più robusto
    ```

3.  **Ottimizzazione per HA 2026.5 & ApexCharts 2.1.x:** 
    - Lo `state: "ok"` nel sensore helper garantisce la validazione corretta.
    - `ignore_history: true` previene l'errore di configurazione su sensori senza storico numerico.
    - `update_interval: 60s` assicura l'aggiornamento dei dati indipendentemente dalla storia.
    - `xaxis: type: category` è necessario per mappare correttamente le etichette testuali (nomi device).
    - Il formato di ritorno `[x, y]` è preferibile per la compatibilità con l'asse categorico.

---
*Ultimo aggiornamento: 1 Giugno 2026*
