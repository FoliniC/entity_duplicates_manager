# Entity Duplicates Manager

![GitHub release](https://img.shields.io/github/v/release/FoliniC/entity_duplicates_manager)
![GitHub](https://img.shields.io/github/license/FoliniC/entity_duplicates_manager)
![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)

Entity Duplicates Manager is a Home Assistant integration designed to identify, manage, and clean up duplicate entities in your Home Assistant instance. It helps keep your entity registry clean by finding entities with suffix patterns like `_2`, `_3` that often occur when devices are re-added or integrations are reconfigured.

## Features

- **Scan for Duplicates**: Automatically scans your entity registry for potential duplicates based on configurable naming patterns.
- **Interactive Card**: A custom Lovelace card to view results, rename entities ("Fix"), or delete them directly from the dashboard.
- **Configurable Filters**:
  - **Suffix Depth**: Control how deep to look for suffixes (e.g., `_2` to `_10`).
  - **Exclude Patterns**: Prevent specific entities or domains (like `sensor.uptime*`) from being flagged.
- **Safe Operations**:
  - **Fix**: Renames the duplicate entity to a desired ID (e.g., merging it back to the original name).
  - **Delete**: Removes the entity from the registry.
  - **Rename to Base**: Batch rename selected entities back to their base names.
- **Persistent Configuration**: Settings are saved across Home Assistant restarts.
- **Dashboard Sensor**: Real-time duplicate count with detailed attributes.
- **Confirmation Safety**: Optional confirmation switch for deletion operations.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant.
2. Go to "Integrations" > "Explore & Download Repositories".
3. Search for "Entity Duplicates Manager" (or add this repository as a custom repository).
4. Click "Download".
5. Restart Home Assistant.

### Manual Installation

1. Download the `entity_duplicates_manager` folder.
2. Copy it to your `custom_components` directory in Home Assistant.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for "Entity Duplicates Manager".
3. Follow the setup steps.

### Entities Created

After installation, the following entities will be available for configuration:

- `number.suffix_filter_max` - Maximum suffix number to scan for (1-10)
- `text.entity_duplicates_manager_exclude_patterns` - Comma-separated list of wildcard patterns to ignore
- `switch.confirm_deletion` - Require confirmation before deleting entities
- `sensor.duplicates_found` - Shows count of duplicates found with details

## Usage

### Lovelace Card

Add the custom card to your dashboard:

```yaml
type: custom:entity-duplicates-manager-card
```

The card provides:
- Real-time scan button
- Configurable filter settings
- Interactive duplicate list with actions
- Fix/Delete/Rename operations
- Visual feedback and status updates

### Services

The integration exposes the following services:

- `entity_duplicates_manager.scan_duplicates`: Triggers a new scan based on current settings.
- `entity_duplicates_manager.fix_entity`: Renames an entity.
- `entity_duplicates_manager.delete_entity`: Deletes an entity.
- `entity_duplicates_manager.rename_entities_to_base`: Batch rename entities to base names.

### Settings

You can adjust the scan behavior via the created entities:

- `number.suffix_filter_max`: Max suffix number to scan for.
- `text.exclude_patterns`: Comma-separated list of wildcard patterns to ignore.
- `switch.confirm_deletion`: Enable confirmation before deletion.

## How It Works

The integration scans all entities in your Home Assistant instance looking for entity IDs ending with numeric suffixes (`_2`, `_3`, etc.). When found, it groups them by their base name and presents them for review.

**Example:**
- `sensor.temperature_2` → base: `sensor.temperature`
- `sensor.temperature_3` → base: `sensor.temperature`

You can then choose to:
- **Fix**: Rename `sensor.temperature_2` to `sensor.temperature` (merging)
- **Delete**: Remove `sensor.temperature_2` from registry
- **Rename to Base**: Automatically rename selected entities to their base names

## Advanced Features

### Persistent Storage
Configuration is automatically saved to `/config/entity_duplicates_manager/config.json` and restored on restart.

### Smart Exclusions
Supports wildcard patterns:
- `sensor.uptime*` - excludes all uptime sensors
- `group.*` - excludes all group entities
- `input_boolean.sel_%` - excludes specific patterns

### Safety Features
- Confirmation switch prevents accidental deletions
- Statistics purging before entity replacement
- Registry validation before operations
- Event size limits for stability

### Dashboard Integration
- Real-time duplicate count sensor
- Detailed attributes with duplicate list
- Configuration display in attributes
- State persistence across restarts

## Development

### Project Structure

```
entity_duplicates_manager/
├── custom_components/entity_duplicates_manager/
│   ├── __init__.py           # Main integration setup
│   ├── config_flow.py        # Configuration flow
│   ├── const.py              # Constants
│   ├── scanner.py            # Duplicate scanning logic
│   ├── storage.py            # Persistent configuration
│   ├── services.yaml         # Service definitions
│   ├── sensor.py             # Duplicate count sensor
│   ├── switch.py             # Confirmation switch
│   ├── number.py             # Suffix filter number
│   ├── text.py               # Exclude patterns text
│   ├── manifest.json         # Integration manifest
│   ├── translations/         # Localization files
│   └── www/                  # Lovelace card frontend
├── .github/workflows/        # CI/CD pipelines
├── README.md                 # This file
├── changelog.md              # Version history
├── hacs.json                 # HACS configuration
└── info.md                   # Additional information
```

### Key Components

- **Scanner** (`scanner.py`): Core duplicate detection with configurable patterns
- **Storage** (`storage.py`): Async JSON-based configuration persistence
- **Platforms**: Sensor, Switch, Number, Text entities for configuration
- **Frontend**: Custom Lovelace card with full interactive UI

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/FoliniC/entity_duplicates_manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/FoliniC/entity_duplicates_manager/discussions)

## Changelog

See [changelog.md](changelog.md) for version history and changes.