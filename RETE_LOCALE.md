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

## Note di Configurazione
- Il server Debian (`192.168.0.3`) funge da centro di controllo sia per la domotica che per i servizi di rete critici (DNS/DHCP tramite AdGuard).
- L'accesso al router OpenWrt è possibile via Web UI (LuCI) o terminale (SSH).

---
*Ultimo aggiornamento: 28 Maggio 2026*
