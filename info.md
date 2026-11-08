# Entity Duplicates Manager - Additional Information

## Project Overview

Entity Duplicates Manager is a Home Assistant custom integration that helps users identify, manage, and clean up duplicate entities in their Home Assistant instance. Duplicate entities commonly occur when devices are re-added, integrations are reconfigured, or entities are recreated with numeric suffixes (_2, _3, etc.).

## Technical Details

### Architecture
- **Integration Type**: Custom Component (Config Entry based)
- **Platforms**: Sensor, Switch, Number, Text
- **Frontend**: Custom Lovelace Card (JavaScript)
- **Storage**: JSON file-based persistence
- **Communication**: Home Assistant Event Bus + Services

### Core Modules

1. **Scanner** (`scanner.py`): Detects duplicates using regex pattern matching
2. **Storage** (`storage.py`): Async configuration persistence
3. **Platforms**: Four entity platforms for configuration UI
4. **Frontend**: Interactive dashboard card

### Data Flow
```
User Action → Service Call → Scanner → Event → Sensor Update → UI Refresh
     ↓
Storage ← Configuration Changes → Platform Entities
```

## Features in Detail

### Duplicate Detection Algorithm
- Scans all entity states in Home Assistant
- Uses regex pattern `(.+)_([0-9]+)$` to identify suffixed entities
- Groups by base name (part before suffix)
- Filters by configurable suffix depth and exclusion patterns
- Distinguishes between registry and state-only entities

### Configuration Management
- **Persistent**: JSON file at `/config/entity_duplicates_manager/config.json`
- **Runtime**: Config entities (number, text, switch) for UI control
- **Fallback**: Reads from `input_number.entity_duplicates_manager_limit` if available
- **Defaults**: Sensible defaults for immediate use

### Safety Mechanisms
1. **Confirmation Switch**: Optional confirmation before deletions
2. **Registry Validation**: Checks entity exists in registry before operations
3. **Target Conflict Resolution**: Purges statistics, removes existing target before rename
4. **Event Size Limits**: 30KB max event payload to prevent recorder issues
5. **Error Recovery**: Graceful handling with detailed logging

### Frontend Capabilities
- Real-time scanning with progress indication
- Interactive duplicate list with entity details
- One-click Fix/Delete/Rename operations
- Configuration controls integrated in card
- Visual feedback for all operations

## Installation Methods

### HACS (Recommended)
Automatic updates, easy management through Home Assistant UI.

### Manual
Copy `custom_components/entity_duplicates_manager/` to HA config directory.

## Configuration Entities

| Entity ID | Type | Purpose | Range/Default |
|-----------|------|---------|---------------|
| `number.suffix_filter_max` | Number | Max suffix to scan | 1-10 (default: 9) |
| `text.entity_duplicates_manager_exclude_patterns` | Text | Exclusion patterns | Comma-separated wildcards |
| `switch.confirm_deletion` | Switch | Deletion confirmation | On/Off (default: Off) |
| `sensor.duplicates_found` | Sensor | Duplicate count + details | Auto-updated |

## Services

| Service | Parameters | Description |
|---------|------------|-------------|
| `scan_duplicates` | `max_suffix`, `exclusion_patterns` | Trigger duplicate scan |
| `fix_entity` | `entity_id`, `new_entity_id` | Rename entity |
| `delete_entity` | `entity_id` | Delete entity |
| `rename_entities_to_base` | `entity_ids[]` | Batch rename to base names |
| `save_settings` | `max_suffix`, `exclusion_patterns` | Save config without scan |
| `exclude_entities` | `entity_ids[]` | Add entities to exclusion list |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `entity_duplicates_manager_scan_complete` | `count`, `duplicates[]`, `config`, `stored_count`, `configured_limit` | Scan results |

## Compatibility

- **Home Assistant**: 2023.1+
- **Python**: 3.11+
- **Dependencies**: None (uses HA core APIs only)
- **Frontend**: Modern browsers with ES6+ support

## Performance

- Scan time: ~1-2 seconds for typical installations (1000+ entities)
- Memory: Minimal, processes in streaming fashion
- Event size: Capped at 30KB for recorder compatibility
- Storage: Single JSON file (~1-5KB)

## Security

- No external network connections
- No authentication required (uses HA permissions)
- Local file storage only
- Service calls respect HA user permissions

## Localization

Translation files in `translations/` directory:
- `en.json` - English (default)
- Additional languages can be added

## Development

### Testing
```bash
# Run integration tests
python -m pytest tests/

# Validate manifest
python -m script.validate_manifest
```

### Building Frontend
Frontend is vanilla JavaScript, no build step required.

## Contributing Guidelines

1. Follow Home Assistant development standards
2. Maintain backward compatibility
3. Add tests for new features
4. Update documentation
5. Follow semantic versioning

## Roadmap

### Planned Features
- [ ] Entity grouping by device/area
- [ ] Automatic scan scheduling
- [ ] Export/import configuration
- [ ] Advanced filtering (by domain, device, area)
- [ ] Statistics dashboard
- [ ] Multi-language support expansion

### Known Limitations
- Single instance only
- Requires HA restart for card registration
- Limited to entity_id pattern matching

## Support

- **Documentation**: This repository's README.md
- **Issues**: GitHub Issues tracker
- **Community**: Home Assistant Community Forum
- **Discord**: Home Assistant Discord #custom-integrations

## License

MIT License - See LICENSE file for details.

## Author

Carlo Folini (FoliniC)
- GitHub: https://github.com/FoliniC
- Repository: https://github.com/FoliniC/entity_duplicates_manager