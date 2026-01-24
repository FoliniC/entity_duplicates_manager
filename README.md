# Entity Duplicates Manager

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Entity Duplicates Manager is a Home Assistant integration designed to identify, manage, and clean up duplicate entities in your Home Assistant instance. It helps keep your entity registry clean by finding entities with suffix patterns like `_2`, `_3` that often occur when devices are re-added or integrations are reconfigured.

## Features

*   **Scan for Duplicates**: Automatically scans your entity registry for potential duplicates based on configurable naming patterns.
*   **Interactive Card**: A custom Lovelace card to view results, rename entities ("Fix"), or delete them directly from the dashboard.
*   **Configurable Filters**:
    *   **Suffix Depth**: Control how deep to look for suffixes (e.g., `_2` to `_5`).
    *   **Exclude Patterns**: Prevent specific entities or domains (like `sensor.uptime*`) from being flagged.
*   **Safe Operations**:
    *   **Fix**: Renames the duplicate entity to a desired ID (e.g., merging it back to the original name).
    *   **Delete**: Removes the entity from the registry.

## Installation

### HACS (Recommended)

1.  Open HACS in Home Assistant.
2.  Go to "Integrations" > "Explore & Download Repositories".
3.  Search for "Entity Duplicates Manager" (or add this repository as a custom repository).
4.  Click "Download".
5.  Restart Home Assistant.

### Manual Installation

1.  Download the `entity_duplicates_manager` folder.
2.  Copy it to your `custom_components` directory in Home Assistant.
3.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for "Entity Duplicates Manager".
3.  Follow the setup steps.

## Usage

### Lovelace Card

Add the custom card to your dashboard:

```yaml
type: custom:entity-duplicates-manager-card
```

### Services

The integration exposes the following services:

*   `entity_duplicates_manager.scan_duplicates`: Triggers a new scan based on current settings.
*   `entity_duplicates_manager.fix_entity`: Renames an entity.
*   `entity_duplicates_manager.delete_entity`: Deletes an entity.

### Settings

You can adjust the scan behavior via the created entities:

*   `number.suffix_filter_max`: Max suffix number to scan for.
*   `text.exclude_patterns`: Comma-separated list of wildcard patterns to ignore.
