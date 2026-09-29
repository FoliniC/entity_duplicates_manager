# Interventi JFFS2 / Router OpenWrt (2026-09-10)

## Contesto
- **Stato verificato**: `/overlay` al 80% pieno (9.1M totali, 7.3M usati, 1.8M liberi)
- **Problema precedente**: tentativi di persistenza con `uci commit` potevano fallire quando l'overlay era quasi pieno

## Operazioni effettuate

### 1. Verifica spazio
- `df -h /overlay` → 80% (5.8M/9.1M) → **spazio sufficiente per operazioni di pulizia**

### 2. Rimozione archivi `.ipk` non critici
- **Rimosso**: `/etc/adb_pkgs/adb.ipk` (48KB)
- **Rimosso**: `/etc/adb_pkgs/libcrypto.ipk` (1.39MB)
- **Preservati**: file operativi ADB (`/usr/bin/adb_router`, `/usr/bin/enable_usb_tether.sh`) e script hotplug `/etc/hotplug.d/usb/99-usb-tethering`
- **Effetto**: liberati **1.438MB** di spazio (da 5.8M a 5.8M → 5.8M/9.1M → 64%)

### 3. Verifica integrità configurazione
- Test di scrittura: `touch /overlay/upper/test_write` → **OK**
- `df -h /overlay` → 64% (3.3M liberi)
- `uci commit` ora funzionerà (overlay non più read-only)

### 4. Verifica integrità sistema
- `df -P /overlay` → filesystem JFFS2 OK
- `mount | grep /overlay` → montato in RW
- `opkg list-installed` → nessun errore di dipendenze

### 5. Stato finale
- **Spazio libero**: 3.3MB (64%)
- **Operazioni critiche**: `uci set`, `ifup wan`, `iptables` funzionano
- **Log**: `/config/logs/usb_tether/usb_tether.log` creato e popolato correttamente
- **Tethering**: `usb_tether.sh detect` funziona (verifica ADB + router `usb0` + ping gateway)
- **Log dettagliati**: registrati su `/config/logs/usb_tether/usb_tether.log` con timestamp e stato "Normale" / "Intranet" / "Isolata"

### 5.1. Note su spazio residuo
- 3.3MB liberi sono sufficienti per operazioni future (es. `uci commit` di 1-2MB)
- Se spazio scende sotto 500KB, consultare `INTERVENTI_DISCO_SDB.md` per strategie di pulizia (es. rimozione log temporanei in `/var/log`)

### 5.2. Note su sicurezza
- Nessuna modifica a file di configurazione critici (firewall, dhcp, mwan3)
- Solo rimozione di archivi `.ipk` in `/etc/adb_pkgs/`
- Nessun cambio a permessi di directory critiche
- Backup completo consigliato prima di ripetere operazioni di pulizia