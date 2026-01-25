# Entity Duplicates Manager

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Entity Duplicates Manager is a Home Assistant integration designed to identify, manage, and clean up duplicate entities in your Home Assistant instance. It helps keep your entity registry clean by finding entities with suffix patterns like `_2`, `_3` that often occur when devices are re-added or integrations are reconfigured.

## Features

*   **Scan for Duplicates**: Automatically scans your entity registry for potential duplicates based on configurable naming patterns.
*   **Interactive Management Card**: A powerful Lovelace card to view results, manage settings, and perform actions.
*   **Advanced Filtering**: 
    *   Support for the `%` wildcard in search filters (e.g., `sensor.%_2`).
    *   Configurable **Suffix Depth** (optional, leave empty to scan all).
    *   Configurable **Exclusion Patterns** (e.g., `switch_%, group.%`).
*   **Permanent Exclusions**: Select specific entities to be permanently hidden from all future scans.
*   **Intelligent Renaming**: Automatically cleans up the entity's Friendly Name during the "Fix" process if it contains the old suffix.
*   **Persistent Storage**: Settings and exclusions are stored safely in `/config/entity_duplicates_manager/config.json`, preserving them during updates.
*   **Internationalization**: Full support for **English** and **Italian**.

## Installation

### HACS (Recommended)

1.  Open HACS in Home Assistant.
2.  Go to "Integrations" > "Explore & Download Repositories".
3.  Search for "Entity Duplicates Manager" (add this repository as a custom repository if not found).
4.  Click "Download".
5.  Restart Home Assistant.

### Manual Installation

1.  Download the `entity_duplicates_manager` folder from `custom_components`.
2.  Copy it to your `custom_components` directory in Home Assistant.
3.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for "Entity Duplicates Manager".
3.  Follow the setup steps.

## Usage

### Lovelace Card

You can easily add the management interface to your dashboard using the **Card Picker**:

1.  Edit your Dashboard.
2.  Click **Add Card**.
3.  Search for **Entity Duplicates Manager**.
4.  The card supports the Visual Editor for a seamless setup.

Alternatively, via YAML:
```yaml
type: custom:entity-duplicates-manager-card
```

### Key Operations

*   **SCAN**: Start a search based on current Max Suffix and Exclusion patterns.
*   **EXCLUDE**: Permanently hide selected entities from future scan results.
*   **FIX**: Rename the duplicate entity back to its base ID (merging it).
*   **DELETE**: Permanently remove the selected entities from the registry.
*   **WILDCARD**: Use `%` in filters to match any string of characters.

## Data Persistence

Configuration and exclusion lists are stored in:
`{your_config_dir}/entity_duplicates_manager/config.json`
This file is NOT deleted when the integration is updated.