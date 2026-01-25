# Changelog

## 1.0.31
*   Fixed "Max Suffix" field resetting to default when cleared.
*   Improved input handling for empty configurations.

## 1.0.30
*   Internationalization: Added full support for English and Italian.
*   Frontend Minification: Optimized card loading performance using Terser.
*   Linting: Fixed JS warnings and improved code quality.

## 1.0.28
*   Fixed "Blocking Call" warnings: Offloaded I/O operations to the executor.
*   Asynchronous storage management for better stability.

## 1.0.21
*   Wildcard Support: Introduced `%` joker in search and detail filters.
*   Improved Regex matching for entity IDs.

## 1.0.18
*   Dynamic List Filtering: Added search box above the duplicate list.
*   Contextual "All/None" selection: Buttons now only affect visible items.

## 1.0.17
*   Persistent Storage: Moved configuration to `/config/entity_duplicates_manager/` to prevent data loss during updates.
*   Exclusion Management: Added ability to permanently exclude specific entities.

## 1.0.13
*   Shadow DOM Refactoring: Fixed layout issues and ensured 100% width.
*   Lovelace UI Improvements: Buttons are now more visible (raised style).
*   Added Card Picker metadata support.

## 1.0.0
*   Initial release.
*   Implemented duplicate scanner logic.
*   Added `fix` and `delete` services.
*   Added custom Lovelace card for management.