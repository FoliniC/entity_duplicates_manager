# Fancoil System Persistence Architecture

## Overview

This fancoil system uses a **unified persistence approach** based on Home Assistant's native capabilities:

1. **Input Helpers** for user-configurable values (automatically persisted by HA)
2. **Trigger-Based Template Sensors** for calculated/derived values that need to survive reboots

## Persistence Strategy

### What Persists Automatically (Input Helpers)

All user-configurable settings are stored as `input_*` helpers, which Home Assistant automatically persists across reboots:

**Per-Room Settings:**
- `input_number.fancoil_{room}_setpoint` - Local setpoint when not following master
- `input_number.fancoil_{room}_sp_offset` - Temperature offset from master
- `input_boolean.fancoil_{room}_enabled` - Enable/disable automation
- `input_boolean.fancoil_{room}_sp_follow_master` - Follow master setpoint
- `input_boolean.fancoil_{room}_hvac_mode_follow_master` - Follow master HVAC mode
- `input_boolean.fancoil_{room}_logging_enabled` - Enable logging
- `input_boolean.fancoil_{room}_logging_follow_master` - Follow master logging setting
- `input_select.fancoil_{room}_hvac_mode_local` - Local HVAC mode
- `input_datetime.fancoil_{room}_last_main_on` - Timestamp of last main switch ON
- `input_datetime.fancoil_{room}_last_main_off` - Timestamp of last main switch OFF

**Global Settings:**
- `input_number.master_setpoint_heat` - Global heating setpoint
- `input_number.master_setpoint_cool` - Global cooling setpoint
- `input_number.fan_distance_*` - Fan speed thresholds
- `input_number.fancoil_resume_delay_minutes` - Delay before resume after STOP
- `input_number.circuit_temp_threshold_*` - Circuit temperature thresholds
- `input_select.fancoil_system_hvac_mode` - Master HVAC mode
- `input_select.fancoil_verbosity_level_master` - Logging verbosity
- `input_boolean.fancoil_logging_master_enabled` - Master logging enable

### What Persists via Trigger-Based Templates

Calculated sensors that derive their value from multiple sources and need to survive reboots:

**Per-Room Calculated Values:**
- `sensor.fancoil_{room}_last_temperature` - Last known good temperature reading
- `sensor.fancoil_{room}_hvac_temp_mode` - Current HVAC mode (considering follow master)
- `sensor.fancoil_{room}_temperature_difference` - Delta between current temp and setpoint

These sensors use the **trigger-based template** pattern:
```yaml
trigger:
  - trigger: state
    entity_id: sensor.source_entity
  - trigger: homeassistant
    event: start
sensor:
  - name: "Persistent Sensor"
    state: >-
      {% set current = states('sensor.source_entity') %}
      {% if current not in ['unavailable', 'unknown', None] %}
        {{ current | float(0) }}
      {% else %}
        {% set old = states('sensor.persistent_sensor') %}
        {{ old | float(default_value) if old not in ['unavailable', 'unknown'] else default_value }}
      {% endif %}
```

### Benefits of This Approach

1. **Native HA Persistence**: No external files or Pyscript needed
2. **Atomic Updates**: Each value updates independently
3. **Failure Resilient**: Sensors fall back to last known value if source becomes unavailable
4. **Startup Resilient**: Values available immediately after restart
5. **Simple**: Uses only built-in HA features

### Migration from Old System

The old system used:
- Pyscript with JSON files for state persistence
- Manual save/restore automations
- File I/O operations

The new system eliminates:
- `pyscript/fancoil_events_write.py` (replaced with system_log.write)
- All `fancoil_state_save` and `fancoil_states_restore` automations
- JSON file reads/writes

All values now persist automatically through HA's native mechanisms.

## File Structure
````
yaml_generator/
├── templates/
│   ├── fancoil_persistence.j2           # Trigger-based template sensors
│   ├── fancoil_room_input_booleans.j2   # Per-room boolean helpers
│   ├── fancoil_room_input_numbers.j2    # Per-room number helpers
│   ├── fancoil_room_input_selects.j2    # Per-room select helpers
│   ├── fancoil_room_input_datetime.j2   # Per-room datetime helpers
│   ├── fancoil_master_input_*.j2        # Master-level helpers
│   └── ...
├── managed_persistence/                  # Generated trigger-based sensors
│   ├── cucina_persistence.yaml
│   ├── camera_grande_persistence.yaml
│   └── ...
├── input_boolean/
│   └── generated_input_booleans.yaml
├── input_number/
│   └── generated_input_numbers.yaml
├── input_select/
│   └── generated_input_selects.yaml
└── input_datetime/
    └── generated_input_datetime.yaml
````

## KNX Write-Only Switch State Recovery

The KNX switches `switch.attiva_pdc` and `switch.attiva_pompa_circolazione` are **write-only** (no `state_address`). They default to OFF after HA restart, which would trigger `GLOBAL DISABLED` and close all valves.

**Recovery mechanism**: Uses `binary_sensor.pdc_heating` (has `state_address` + `sync_state`) as the authoritative source — it reads real KNX state and persists via HA `restore_state`.

See: `automations/restore_pdc_switches_on_startup.yaml` and `SISTEMA_CLIMATIZZAZIONE.md` → "Ripristino stato all'avvio"

## Maintenance

### Adding New Persistent Values

For user settings: Add to appropriate input_* template (e.g., fancoil_room_input_numbers.j2)
For calculated values: Add to fancoil_persistence.j2 as trigger-based sensor

### Regenerating Files

```bash
python3 yaml_generator/generate_fancoil_climates.py
```

Then reload:
- Template entities
- Input helpers
- Automations

### Troubleshooting

**Q: Values reset after restart?**
- Check that input helpers are properly defined
- Verify trigger-based sensors have homeassistant startup trigger

**Q: Sensors show 'unknown' after restart?**
- Normal for first few seconds
- Should resolve when source entities become available
- Check trigger conditions in persistence template

**Q: Need to reset all values?**
- Delete `.storage/core.restore_state` (HA will recreate)
- Or set values manually via UI