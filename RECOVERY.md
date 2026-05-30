# Recovery Log - Manual Fix for State Overrides

## Operation: Grace Period Implementation
**Date**: 2026-05-30
**Target**: `pyscript/halog2026_events_write.py`

### Backup of Original Files
- `cp /home/carlo/docker/homeassistant/config/pyscript/halog2026_events_write.py /home/carlo/docker/homeassistant/config/backups/manual_fix_deumidificazione/halog2026_events_write.py.bak`

### Change Description
Added a check to compare the `last_changed` attribute of the entity with the current time. If the entity has been updated within the last 300 seconds (5 minutes), the automatic state restore triggered by HALog2026 is skipped to respect manual user overrides.

### Rollback Instructions
To rollback, simply restore the original file from the backup:
```bash
cp /home/carlo/docker/homeassistant/config/backups/manual_fix_deumidificazione/halog2026_events_write.py.bak /home/carlo/docker/homeassistant/config/pyscript/halog2026_events_write.py
```
