# GEMINI.md - Team Instructions & Project Mandates

## 📌 Development Standards
- **Architectural Pattern**: Unified persistence for fancoil system using native HA helpers.
- **Conventions**: Adhere to the existing YAML structure and naming conventions.
- **Testing**: Empirical reproduction of failures is mandatory before applying fixes.
- **Validation**: After modifying any YAML configuration, ALWAYS run the configuration check:
  `docker exec homeassistant hass --script check_config -c /config`

## 📁 Logging & Maintenance (HALog2026)
Custom logs are centrally managed by the **HALog2026** event-based system.
- **Config file**: `/config/logs/halog2026_config.json`
- **Library**: `/config/pyscript/lib/halog2026_lib.py`

### Log Locations:
- **Fancoil Events**: `/config/logs/fancoil_events/fancoil_events.log` (Event: `fancoil_log_event`)
- **EV Events**: `/config/logs/EV/ev_events.log` (Event: `ev_log_event`)
- **Scale Events**: `/config/logs/scale/scale_events.log` (Event: `scale_log_event`)

### How to log from YAML:
```yaml
action:
  - event: fancoil_log_event
    event_data:
      level: INFO
      message: "Your message"
```

### Troubleshooting Window Alerts:
- Window alerts use temperature and humidity variance.
- Logs can be searched for `custom_components.window_alert` in the standard HA log.
- Conditions include a thermal delta check (> 5°C difference with `sensor.temperatura_strenscia`).

### MG SAIC Integration:
- **Startup Resilience**: The integration is configured to avoid blocking HA startup. If the cloud is unreachable during boot, it uses `ConfigEntryNotReady` to defer setup.
- **Persistent Fix**: Do not replace the `CoreState.starting` check with `asyncio.sleep` as it blocks the boot sequence.

## 🚀 Deployment Info
- Backup script: `/usr/local/bin/ha_gh_backup` (managed by `ha-gh-backup.timer`).
- Authentication: Root SSH key (`/root/.ssh/id_rsa`).
- Host Control: Dedicated SSH key at `/config/.ssh/host_key` used by shell commands to control host Docker containers.
- documentation: `/config/GITHUB_BACKUP.md`.
- Rete Locale: `/config/RETE_LOCALE.md`.
- Alexa: `/config/alexa.md`.
- Ottimizzazione Telefono: `/config/OTTIMIZZAZIONE_TELEFONO.md`.
- Interventi Router JFFS2: `/config/INTERVENTI_JFFS2_ROUTER.md`.
- Interventi Disco SDB: `/config/INTERVENTI_DISCO_SDB.md`.
- Analisi Tethering USB: `/config/ANDROID_NOTE11_ROUTER_USB_TETHERING_ANALYSIS.md`.
- ADB TCP 5555 Success: `/config/ADB_TCPIP_5555_SUCCESS.md`.
- ADB Wireless Attempt (fallito): `/config/ADB_WIRELESS_ATTEMPT.md`.
- Diagnostica Honor: `/config/DIAGNOSTICA_HONOR_COL-L29_PRE_OTTIMIZZAZIONE.md`.
- Diagnostica Redmi: `/config/DIAGNOSTICA_REDMI_NOTE_9S_PRE_OTTIMIZZAZIONE.md`.
- Telecamere / Frigate: `/config/TELECAMERE.md`.
- Tuya / Handshake: `/config/tuya_handshake.md`.
- Tuya Balcone Cloud Interception: `/config/TUYA_BALCONE_CLOUD_INTERCEPTION.md`.
- Recupero / Backup: `/config/RECOVERY.md`.
- Monitoraggio Rete: `/config/README_MONITOR.md`.
- Ottimizzazione Telefono (post): `/config/OTTIMIZZAZIONE_HONOR_COL-L29_POST_IP_CAMERA.md`.
- Config Samba: `/config/samba_config.md`.
- Monitoraggio Bluetooth M5 Atom: `/config/M5_ATOM_ECHO_BT_PROXY_SETUP.md`.
- Pianificazione Clima: `/config/PIANO_CLIMATIZZAZIONE_FINESTRE_UMIDITA.md`.
- Setup Xiaomi BLE: `/config/XIAOMI_BLE_SETUP.md`.
- Cloudflare Tunnel: `/config/troubleshoot_cloudflare_tunnel.md`.


## 🔌 SSH verso l'Host da shell_command

Il container Home Assistant **non ha il binary `docker`** nel suo filesystem.
Qualsiasi `shell_command` che invoca `docker` direttamente fallirà con **return code 127** ("command not found").

**Regola**: Usare sempre SSH verso l'host tramite la chiave dedicata per controllare i container Docker.

- **Host IP**: `192.168.0.3`
- **Utente**: `carlo`
- **Chiave SSH**: `/config/.ssh/host_key`

### Pattern corretto per shell_command:
```yaml
# ✅ CORRETTO — SSH verso l'host
my_command: "ssh -i /config/.ssh/host_key -o StrictHostKeyChecking=no carlo@192.168.0.3 'docker start my-container'"

# ❌ SBAGLIATO — docker non esiste nel container HA (return code 127)
my_command: "docker start my-container"
```

### Test rapido di connettività SSH:
```bash
docker exec homeassistant ssh -i /config/.ssh/host_key -o StrictHostKeyChecking=no carlo@192.168.0.3 'docker ps'
```

## 🤖 Google Antigravity CLI (agy)
- **Installazione / Aggiornamento**:
  - Comando rapido da terminale: `agy update`
  - In alternativa, eseguire lo script di aggiornamento locale: `/config/update_antigravity.sh` (rende automatica l'installazione delle dipendenze come `curl` e il download del binario ufficiale).
  - Script ufficiale di installazione: `curl -fsSL https://antigravity.google/cli/install.sh | bash`
- **Verifica versione**: `agy --version`
