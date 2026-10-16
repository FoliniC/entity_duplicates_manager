# HA DB Verification & Template Sensor Pitfalls (2026-10-15 session)

## Pitfall: Checking wrong recorder database

**Rule**: Before querying `home-assistant_v2.db` (SQLite), verify `recorder.yaml` (`/config/recorder.yaml` or `/config/configuration.yaml`) for `db_url`. If it points to `mysql://...`, the active DB is MariaDB on `192.168.0.3:3306`, NOT the SQLite file.

**Why**: HA Docker setups often mount both a SQLite file (default or backup) and configure MariaDB via `db_url`. The SQLite file (`/config/home-assistant_v2.db`) may contain stale or partial data. Querying it produces false negatives (e.g., "entity not in DB" when the entity exists in MariaDB with full history).

**Verification commands**:
```bash
# Check active DB from HA config
cat /config/recorder.yaml | grep db_url
# Check MariaDB container status
docker ps | grep mariadb
# Check MariaDB for entity meta/state
docker exec mariadb mysql -h192.168.0.3 -uhomeassistant -p... -P3306 homeassistant -e "SELECT entity_id FROM states_meta WHERE entity_id LIKE '%envoy_...%'; SELECT entity_id, state, last_updated FROM states WHERE entity_id = 'sensor.produzione_solare' ORDER BY last_updated DESC LIMIT 1;"
```

**Evidence from session**: The CSV (`history (1).csv`) showed thousands of `produzione_solare` records (values from -8W to +3927W, dates 2026-10-11 to 2026-10-14), confirming MariaDB stores historical state. SQLite showed zero rows for the same entity. The SQLite DB (`/config/home-assistant_v2.db`) was the wrong target.

## Pitfall: Template sensor fails but source works

**Rule**: When a derived `template:` sensor (e.g., `ev_charge_2025_current_soc`) returns `unavailable` but its source entity (e.g., `piazzale_mg_mg4_electric_state_of_charge`) has a valid value (`69.7`% or `66.0`%), prefer using the source entity directly in the dashboard/card rather than relying on the derived template.

**Why**: Template sensors (`template:` integration in HA 2026+) use `- name:` format (`template:` block with `- name:` items, NOT `- platform: template`). Even with correct syntax, the template may not reload properly across HA restarts, especially when the source entity updates from a cloud integration (`mg_saic`) with intermittent timeout/retry behavior. The derived sensor adds a failure point (template reload, `is_number()` checks, fallback logic) that the direct source avoids.

**Verification**: Check source entity state directly (`states('sensor.piazzale_mg...')`) vs derived (`states('sensor.ev_charge...')`). If the source is `69.7`% and the derived is `unavailable`, the template hasn't been re-evaluated.

**Fix hierarchy**:
1. Verify source entity (`states()` in markdown/debug card)
2. If source works → modify dashboard card (`entity:`) to use source directly
3. Only rely on derived template for multi-source aggregation when both sources are verified active

**From session**: The fix applied changed the dashboard gauge from `entity: sensor.ev_charge_2025_current_soc` (derived template) to `entity: sensor.piazzale_mg_mg4_electric_state_of_charge` (direct MG SAIC source). The template sensor (`ev_charge_2025_current_soc`) was left as-is but the card bypasses it.

## HACS version tracking vs manifest

**Rule**: HACS tracks installed version in `.storage/hacs.data` (`version_installed`, `installed_commit`), separate from `manifest.json` (`version` field). Updating `manifest.json` alone does not update HACS tracking.

**Fix**: After upgrading a component, update `.storage/hacs.data` to match the new `version_installed` and `installed_commit` (e.g., `1.3.0` / `3860391`), then restart HA and verify in HACS UI.

**From session**: `manifest.json` showed `1.3.0` with `mg-saic-client==0.9.6` and `mg-ismart-india-client==0.2.0`. HACS `.storage/hacs.data` initially showed `version_installed: 1.1.4` / `installed_commit: 409b4bd`. Updating the HACS fields resolved the version mismatch.
