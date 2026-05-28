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
  - **Base (Cucina):** Collegata via Ethernet Gigabit al router TP-Link.
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
L'integrazione del sistema Tenda Mesh5 ha un impatto significativo sulla stabilità dei dispositivi Echo:

1.  **Backhaul Ethernet:** La base in cucina collegata via cavo garantisce che il traffico generato dalle Alexa in quell'area non consumi banda Wi-Fi aggiuntiva per il transito verso il router.
2.  **Roaming (Camera):** `alexa-camera` potrebbe trovarsi in una zona di sovrapposizione tra la 5GHz del router TP-Link e il satellite Tenda in camera. Se le due reti hanno lo stesso SSID, il dispositivo potrebbe saltare tra i due, causando micro-disconnessioni.
3.  **Interferenza Canali:** Il sistema Tenda Mesh tende a scegliere canali automaticamente. È fondamentale che il router OpenWrt usi un canale fisso (es. 36-48) per evitare che il Mesh entri in conflitto sulla stessa frequenza 5GHz.
4.  **Latenza:** I satelliti wireless (Balcone/Camera) aggiungono un leggero ritardo (latenza) rispetto alla connessione diretta al router o alla base cablata.

## Note di Configurazione
- Il server Debian (`192.168.0.3`) funge da centro di controllo sia per la domotica che per i servizi di rete critici (DNS/DHCP tramite AdGuard).
- L'accesso al router OpenWrt è possibile via Web UI (LuCI) o terminale (SSH).

---
*Ultimo aggiornamento: 28 Maggio 2026*
