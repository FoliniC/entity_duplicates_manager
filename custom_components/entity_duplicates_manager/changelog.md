# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-11-07

### Added
- **Persistent Storage System** (`storage.py`): Async JSON-based configuration persistence with automatic load/save
- **Enhanced Scanner** (`scanner.py`): Advanced duplicate detection with configurable limits, pattern matching, and source tracking
- **Dashboard Sensor** (`sensor.py`): Real-time duplicate count with RestoreEntity support and detailed attributes
- **Confirmation Switch** (`switch.py`): Safety switch to prevent accidental deletions
- **Suffix Filter Number** (`number.py`): Configurable max suffix depth (1-10) with persistence
- **Exclude Patterns Text** (`text.py`): Wildcard pattern management for exclusions
- **Custom Lovelace Card** (`www/entity_duplicates_manager_card/`): Full interactive frontend with scan, fix, delete, and rename operations
- **Batch Rename Service**: `rename_entities_to_base` service for bulk operations
- **Configuration Flow** (`config_flow.py`): Single-instance configuration flow
- **Advanced Safety Features**: Statistics purging, registry validation, event size limits
- **Multi-source Configuration**: Reads from both persistent storage and input_number entities

### Changed
- **Core Integration** (`__init__.py`): Complete rewrite with storage integration, event handling, and service management
- **Constants** (`const.py`): Extended with additional service names and event types
- **Manifest** (`manifest.json`): Updated to v1.2.0 with enhanced metadata

### Fixed
- Entity registry operations now handle target conflicts gracefully
- Event payload size limited to prevent recorder issues
- State persistence across Home Assistant restarts
- Wildcard pattern matching for exclusions

## [1.1.0] - 2026-02-11

### Added
- Initial HACS support
- Basic duplicate scanning functionality
- Simple fix and delete services
- Entity registry integration

### Changed
- Improved scanning algorithm
- Better error handling

## [1.0.0] - 2026-01-25

### Added
- Initial release
- Basic duplicate detection
- Entity rename and delete services
- GitHub repository setup

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.2.0 | 2026-11-07 | Major enhancement with persistent storage, UI, and safety features |
| 1.1.0 | 2026-02-11 | HACS support and stability improvements |
| 1.0.0 | 2026-01-25 | Initial release |

## Upgrade Notes

### From 1.1.0 to 1.2.0
- **Breaking**: Configuration now uses persistent storage (`/config/entity_duplicates_manager/config.json`)
- **New Entities**: Four new configuration entities added automatically
- **Enhanced UI**: New Lovelace card available as `custom:entity-duplicates-manager-card`
- **Services**: Added `rename_entities_to_base` for batch operations
- **Compatibility**: Existing configurations will be migrated automatically on first run