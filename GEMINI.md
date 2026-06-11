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
- documentation: `/config/GITHUB_BACKUP.md`.
- Rete Locale: `/config/RETE_LOCALE.md`.

