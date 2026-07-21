# Configurazione Samba - Home Assistant Server

## Panoramica
Server Samba in esecuzione su **192.168.0.3** (container Docker `dperson/samba`) per condivisione file SMB/CIFS accessibile da **192.168.0.8** (Windows 11).

---

## Informazioni di Connessione

| Parametro | Valore |
|-----------|--------|
| **Server** | `192.168.0.3` |
| **Hostname** | `samba` (container) |
| **Workgroup** | `MYGROUP` |
| **Porte** | `139` (NetBIOS), `445` (SMB diretto) |
| **Protocollo** | SMB 2.10 – 3.0 (compatibile Windows 11) |

---

## Credenziali di Accesso

| Campo | Valore |
|-------|--------|
| **Utente** | `carlo` |
| **Password** | `casacp` |
| **UID/GID** | `1000:1000` (mappato su host) |

---

## Share Disponibili

### 1. `config` — Configurazione Home Assistant
| Proprietà | Valore |
|-----------|--------|
| **Percorso UNC** | `\\192.168.0.3\config` |
| **Percorso container** | `/config` |
| **Percorso host** | `/home/carlo/docker/homeassistant/config` |
| **Read-only** | No |
| **Browsable** | Sì |
| **Valid users** | `carlo` |
| **Veto files** | `.apdisk`, `.DS_Store`, `.TemporaryItems`, `.Trashes`, `desktop.ini`, `ehthumbs.db`, `Network Trash Folder`, `Temporary Items`, `Thumbs.db` |

### 2. `home` — Home Directory Utente
| Proprietà | Valore |
|-----------|--------|
| **Percorso UNC** | `\\192.168.0.3\home` |
| **Percorso container** | `/home_carlo` |
| **Percorso host** | `/home/carlo` |
| **Read-only** | No |
| **Browsable** | Sì |
| **Valid users** | `carlo` |
| **Veto files** | Stessi di `config` |

---

## Configurazione Container (docker-compose.yml)

```yaml
services:
  samba:
    image: dperson/samba
    container_name: samba
    restart: unless-stopped
    ports:
      - "139:139"
      - "445:445"
    volumes:
      - ./homeassistant/config/custom-cont-init.d:/custom-cont-init.d
      - ./homeassistant/config:/config
      - /home/carlo:/home_carlo
    command: >
      -u "carlo;casacp;1000"
      -s "config;/config;yes;no;no;carlo"
      -s "home;/home_carlo;yes;no;no;carlo"
```

> **Nota**: Non si usano `USERID`/`GROUPID` nelle environment variables perché l'immagine `dperson/samba` crea internamente l'utente `smbuser` con UID 1000. Specificare UID 1000 causava conflitto. La soluzione funzionante omette le env vars e passa direttamente UID 1000 nel comando `-u`.

---

## smb.conf Generato (estratto rilevante)

```ini
[global]
   workgroup = MYGROUP
   server string = Samba Server
   server role = standalone server
   log file = /dev/stdout
   max log size = 50
   dns proxy = no
   
   # Sicurezza
   pam password change = yes
   map to guest = bad user
   usershare allow guests = yes
   
   # Permessi file/directory
   create mask = 0664
   force create mode = 0664
   directory mask = 0775
   force directory mode = 0775
   force user = smbuser
   force group = smb
   
   # Protocolli SMB
   client ipc max protocol = SMB3
   client ipc min protocol = SMB2_10
   client max protocol = SMB3
   client min protocol = SMB2_10
   server max protocol = SMB3
   server min protocol = SMB2_10
   
   # Time Machine / macOS
   fruit:delete_empty_adfiles = yes
   fruit:time machine = yes
   vfs objects = catia fruit recycle streams_xattr

[config]
   path = /config
   browsable = yes
   read only = no
   guest ok = no
   valid users = carlo
   veto files = /.apdisk/.DS_Store/.TemporaryItems/.Trashes/desktop.ini/ehthumbs.db/Network Trash Folder/Temporary Items/Thumbs.db/
   delete veto files = yes

[home]
   path = /home_carlo
   browsable = yes
   read only = no
   guest ok = no
   valid users = carlo
   veto files = /.apdisk/.DS_Store/.TemporaryItems/.Trashes/desktop.ini/ehthumbs.db/Network Trash Folder/Temporary Items/Thumbs.db/
   delete veto files = yes
```

---

## Connessione da Windows 11 (192.168.0.8)

### Metodo 1: Esplora File (GUI)
1. `Win + E` → Barra indirizzi: `\\192.168.0.3` → Invio
2. Credenziali:
   - Utente: `carlo`
   - Password: `casacp`
   - ☑ "Ricorda le mie credenziali"

### Metodo 2: PowerShell (Mappatura Unità Persistente)
```powershell
# Apri PowerShell come Amministratore
net use Z: \\192.168.0.3\config /user:carlo casacp /persistent:yes
net use H: \\192.168.0.3\home  /user:carlo casacp /persistent:yes
```

### Metodo 3: cmd / batch
```cmd
net use Z: \\192.168.0.3\config /user:carlo casacp /persistent:yes
net use H: \\192.168.0.3\home  /user:carlo casacp /persistent:yes
```

### Rimozione mappature
```powershell
net use Z: /delete
net use H: /delete
```

---

## Troubleshooting Windows 11

### Share non visibili / "Errore di rete"
**Causa probabile**: Profilo rete su "Pubblica"  
**Fix**:
1. `Impostazioni` → `Rete e Internet` → `Ethernet` (o Wi-Fi)
2. **Profilo rete** → **Privata**
3. Riavvia Esplora file / riprova `\\192.168.0.3`

### "Accesso negato" / Credenziali errate
1. **Credential Manager**: `Win + R` → `control keymgr.dll` → Rimuovi voci salvate per `192.168.0.3`
2. Riprova con credenziali fresche: `carlo` / `casacp`

### SMB 1.0
> **NON abilitare SMB 1.0** (disabilitato di default in Win 11 per sicurezza).  
> Il server usa SMB 2.10+ nativamente.

### Firewall Windows
Se non connette, verifica regole in entrata:
```powershell
# PowerShell Admin
Enable-NetFirewallRule -DisplayGroup "File and Printer Sharing"
```

---

## Test da Linux / WSL / macOS

```bash
# Lista share
smbclient -L //192.168.0.3 -U carlo%casacp

# Monta share config
sudo mount -t cifs //192.168.0.3/config /mnt/config \
  -o username=carlo,password=casacp,vers=3.0,uid=1000,gid=1000

# Monta share home
sudo mount -t cifs //192.168.0.3/home /mnt/home \
  -o username=carlo,password=casacp,vers=3.0,uid=1000,gid=1000

# Smonta
sudo umount /mnt/config /mnt/home
```

---

## Gestione Container

```bash
# Stato
cd /home/carlo/docker && docker compose ps samba

# Log
cd /home/carlo/docker && docker compose logs samba --tail 50

# Riavvio
cd /home/carlo/docker && docker compose restart samba

# Ricrea (dopo modifiche docker-compose.yml)
cd /home/carlo/docker && docker compose up -d samba

# Shell nel container
docker exec -it samba sh
```

---

## File di Sistema Rilevanti

| Percorso | Descrizione |
|----------|-------------|
| `/home/carlo/docker/docker-compose.yml` | Definizione servizio Samba |
| `/home/carlo/docker/homeassistant/config/` | Share `config` (montato in `/config`) |
| `/home/carlo/` | Share `home` (montato in `/home_carlo`) |

---

## Sicurezza

- ✅ **Nessun accesso guest** (`guest ok = no`)
- ✅ **Solo utente autenticato** (`valid users = carlo`)
- ✅ **SMB signing/encryption** supportato (SMB 3.x)
- ✅ **Veto file** per file di sistema macOS/Windows nascosti
- ✅ **Container non privileged**, user mapping UID 1000
- ⚠️ Password in chiaro in `docker-compose.yml` (solo host trusted)
- ⚠️ Workgroup default `MYGROUP` (cambiare se in dominio)

---

## Changelog

| Data | Versione | Note |
|------|----------|------|
| 2026-07-20 | 1.0 | Configurazione iniziale funzionante con utente `carlo` / `casacp` |

---

*Generato automaticamente - Ultimo aggiornamento: 2026-07-20*