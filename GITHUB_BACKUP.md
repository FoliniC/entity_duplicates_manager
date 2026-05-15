# Sistema di Backup GitHub - Home Assistant

Questo repository viene backuppato automaticamente su GitHub utilizzando un sistema basato su **Systemd Timer** e uno script Bash personalizzato.

## Componenti del Sistema

### 1. Script di Backup
*   **Percorso**: `/usr/local/bin/ha_gh_backup`
*   **Descrizione**: Lo script gestisce l'intero ciclo di vita del backup:
    *   Verifica dello stato del repository (file modificati, commit pendenti).
    *   Aggiunta automatica dei nuovi file (rispettando il `.gitignore`).
    *   Creazione di un commit con timestamp.
    *   Push verso GitHub utilizzando autenticazione SSH.
*   **Autenticazione**: Utilizza la chiave SSH dell'utente root situata in `/root/.ssh/id_rsa`.

### 2. Automazione (Systemd)
Il backup è schedulato tramite due unità systemd:

*   **Timer**: `ha-gh-backup.timer`
    *   Controlla la frequenza di esecuzione (attualmente configurato per girare periodicamente).
    *   Stato: `systemctl status ha-gh-backup.timer`
*   **Service**: `ha-gh-backup.service`
    *   Esegue materialmente lo script come utente root.
    *   Stato: `systemctl status ha-gh-backup.service`

## Comandi Utili

### Verificare i Log
Per controllare l'esito degli ultimi backup:
```bash
sudo journalctl -u ha-gh-backup.service -n 50 --no-pager
```

### Eseguire un Backup Manuale
È possibile forzare l'esecuzione immediata del backup senza attendere il timer:
```bash
sudo systemctl start ha-gh-backup.service
```

### Verificare l'autenticazione GitHub
Per testare se la chiave SSH è ancora valida:
```bash
sudo ssh -T git@github.com
```

## Struttura dello Script
Lo script è diviso in fasi:
- **FASE 0**: Analisi del repository (diff, log).
- **FASE 1**: `git add .` (se ci sono modifiche unstaged).
- **FASE 2**: `git commit` con messaggio "Backup YYYY-MM-DD HH:MM".
- **FASE 3**: `git push` con log dettagliati delle operazioni di rete.

## Note sulla Manutenzione
In caso di errore "128" durante il push, potrebbe esserci un conflitto remoto. In tal caso, potrebbe essere necessario eseguire manualmente un `git pull` o, se si è sicuri della propria versione locale, un `git push --force-with-lease origin main` dalla cartella `/home/carlo/docker/homeassistant/config`.
