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
3.  **Ottimizzazione alexa-cucina:** Agganciata alla base Tenda Mesh (cablata), garantendo stabilità tramite il backhaul ethernet.
4.  **Interferenza Canali:** Il router OpenWrt utilizza il **canale 149 (5GHz)** in modalità **VHT80** (fisso), mentre il Tenda Mesh opera sui canali bassi (es. 40), eliminando le sovrapposizioni.

## Note di Configurazione
- Il server Debian (`192.168.0.3`) funge da centro di controllo sia per la domotica che per i servizi di rete critici (DNS/DHCP tramite AdGuard).
- L'accesso al router OpenWrt è possibile via Web UI (LuCI) o terminale (SSH).

---
*Ultimo aggiornamento: 28 Maggio 2026*
