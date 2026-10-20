# Architettura e Configurazione Desktop Remoto: Guacamole & GNOME Wayland

Questo documento descrive la configurazione implementata per consentire al client **Apache Guacamole** (in esecuzione nello stack Docker / addon di Home Assistant) di visualizzare ed interagire con la **stessa identica sessione grafica locale (GNOME su Wayland)** del PC host fisico (`homeassistant`), anziché generare una sessione virtuale separata (es. XFCE via xrdp).

---

## 1. Panoramica Architetturale

```
[ Browser / App HA ]
         │ (HTTP / WebSockets)
         ▼
[ Guacamole Client (Tomcat) ] ── (Port 4822) ──► [ guacd (Docker) ]
                                                        │
                                                        │ (RDP TCP 3389)
                                                        ▼
                                       [ gnome-remote-desktop-daemon ]
                                                        │ (D-Bus / Mutter)
                                                        ▼
                                           [ Sessione GNOME Wayland ]
                                         (Display :0 - Monitor Fisico)
```

### Perché prima appariva XFCE?
- `xrdp` / `xrdp-sesman` erano attivi sulla porta `3389` e creavano un server grafico virtuale indipendente (`/usr/lib/xorg/Xorg :10`), isolato dal display fisico (`:0`).
- Avendo `xrdp` occupato la porta `3389`, il demone nativo `gnome-remote-desktop` (con opzione `negotiate-port: true`) si era riposizionato automaticamente sulla porta `3390`.
- Guacamole, puntando a `192.168.0.3:3389`, si collegava a `xrdp`, aprendo l'ambiente di default configurato per le sessioni headless (XFCE).

### Soluzione Adottata
- **xrdp disabilitato**: eliminata la duplicazione delle sessioni X11/XFCE.
- **gnome-remote-desktop su porta 3389**: il demone nativo di GNOME ascolta sulla porta standard RDP e condivide via PipeWire/Mutter il display principale Wayland (`mirror-primary`).
- **Guacamole connesso direttamente a GNOME**: parametri ottimizzati a 32 bpp senza vincoli di risoluzione fissa.

---

## 2. Configurazione Host (GNOME Wayland)

### Servizi di Sistema Disabilitati (xrdp)
Per liberare la porta 3389 e prevenire sessioni fantasma:
```bash
sudo systemctl stop xrdp xrdp-sesman
sudo systemctl disable xrdp xrdp-sesman
```

### Demone Utente GNOME Remote Desktop
Il servizio è gestito a livello utente (`carlo`, UID 1000) tramite systemd:
- **Unit**: `gnome-remote-desktop.service`
- **Binario**: `/usr/libexec/gnome-remote-desktop-daemon`
- **Stato**: `systemctl --user status gnome-remote-desktop`

### Impostazioni RDP (`grdctl` & `gsettings`)
Visualizzabili con `grdctl status --show-credentials` o via GSettings:

```ini
[org.gnome.desktop.remote-desktop.rdp]
enable=true
negotiate-port=true
port=uint16 3389
screen-share-mode='mirror-primary'
view-only=false
tls-cert='/home/carlo/rdp-certs/rdp.crt'
tls-key='/home/carlo/rdp-certs/rdp.key'
```

- **Credenziali RDP**:
  - Username: `carlo`
  - Password: `casacp`
  *(configurate tramite `grdctl rdp set-credentials carlo casacp`)*
- **Certificati TLS**:
  - Percorso: `/home/carlo/rdp-certs/` (`rdp.crt` e `rdp.key`)
- **Gestione Schermo e Blocco**:
  - `gsettings set org.gnome.desktop.screensaver lock-enabled false`
  - `gsettings set org.gnome.desktop.session idle-delay 0`

---

## 3. Configurazione Connessione in Guacamole (`guacamole-db`)

La connessione RDP su Guacamole (`connection_id = 2`, nome **`Debian 13 GUI`**) è memorizzata nel database PostgreSQL (`guacamole_db`).

### Parametri Connessione Attuali

| Parametro | Valore | Descrizione |
| :--- | :--- | :--- |
| `hostname` | `192.168.0.3` | IP locale host Debian |
| `port` | `3389` | Porta RDP nativa GNOME |
| `username` | `carlo` | Utente RDP configurato in `grdctl` |
| `password` | `casacp` | Password RDP configurata in `grdctl` |
| `color-depth` | `32` | Profondità colore richiesta dalla pipeline grafica RDP |
| `security` | `any` | Negoziazione TLS/NLA supportata da FreeRDP e GNOME |
| `ignore-cert` | `true` | Accetta il certificato autofirmato in `rdp-certs` |
| `server-layout` | `it-it-qwerty` | Mappatura tastiera italiana |
| `disable-audio` | `true` | Disabilita audio remoto se non necessario |

> [!NOTE]
> I parametri fissi `width` (1280), `height` (720) e `dpi` (96) sono stati **rimossi** per consentire a Guacamole di visualizzare dinamicamente la risoluzione nativa del monitor fisico (1680x1050) senza bande nere o scaling forzato.

---

## 4. Query di Manutenzione e Verifica

### Verificare i parametri correnti nel DB Guacamole
```bash
docker exec guacamole-db psql -U guacamole_user -d guacamole_db -c \
  "SELECT parameter_name, parameter_value FROM guacamole_connection_parameter WHERE connection_id = 2;"
```

### Verificare l'ascolto sulla porta 3389
```bash
ss -tlpn | grep 3389
# Output atteso: LISTEN ... *:3389 ... users:(("gnome-remote-de",...))
```

### Test di connettività dal container `guacd`
```bash
docker exec guacd nc -zv 192.168.0.3 3389
```

### Riavviare il servizio GNOME Remote Desktop
```bash
systemctl --user restart gnome-remote-desktop
```

### Consultare i log in tempo reale
```bash
# Log GNOME Remote Desktop:
journalctl --user -u gnome-remote-desktop -f

# Log guacd:
docker logs guacd -f --tail 50
```
