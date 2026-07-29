# Tuya Cloud ↔ LocalTuya Handshake Protocol

## Expected Behavior of "Aggiungi Nuovo Dispositivo"

The "aggiungi nuovo dispositivo" (add new device) flow in LocalTuya follows this sequence:

1. **Cloud API attempt** — LocalTuya tries to contact the Tuya Cloud API (as implemented in the
   original `hass-localtuya` repo) to fetch the device list.
2. **If cloud fails** (authorization error, network issue, etc.):
   - **No cache exists** → the user is shown a form to paste the raw Tuya Cloud JSON manually.
   - **Cache exists** → the user is shown a 3-option selector:
     - `📂 Use cached device list` — use the previously cached JSON as-is, skip re-fetching.
     - `🔄 Fetch fresh from Tuya Cloud` — re-fetch the device list from Tuya Cloud, update the cache,
       filter out already-configured devices, and proceed.
     - `📝 Paste new JSON` — paste a new JSON payload from the Tuya Cloud API.
3. **Format 1 JSON parsed** (`{"result": {"data": [...]}}`) — the list of `res_id` device IDs is
   filtered to exclude already-configured devices (by cloud ID and MAC address). The remaining
   unconfigured device IDs are stored as `_manual_device_ids` and the user proceeds to step 2.
4. **Step 2: Format 2 JSON** — the user pastes detailed device info JSON
   (`{"result": [...]}` with full device objects including `id`, `local_key`, `ip`, `product_id`,
   `mac`, etc.). A pre-import duplicate check runs before merging into `cloud_data.device_list`:
   - Devices already configured by cloud ID → **skipped**
   - Devices with a MAC that matches an existing configured device → **skipped**
     (catches factory-reset devices that got new cloud IDs but keep the same hardware MAC)
   - If all devices are filtered → `all_devices_configured` error is shown.
   - Otherwise the filtered devices are merged and the individual device configuration form is shown.

## API Endpoint Verification

### Original hass-localtuya (xZetsubou / reference implementation)

| Purpose | Endpoint | HTTP Method |
|---|---|---|
| Authentication | `/v1.0/token?grant_type=1` | GET |
| Get all user devices | `/v1.0/users/{uid}/devices` | GET |
| Get device info | `/v1.0/devices/{device_id}` | GET |
| Get device functions | `/v1.0/devices/{device_id}/functions` | GET |
| Get device specs (fallback) | `/v1.1/devices/{device_id}/specifications` | GET |
| Get space resources | `/v2.0/cloud/space/{space_id}/resource` | GET |
| Get child spaces | `/v2.0/cloud/space/child` | GET |
| Get space info | `/v2.0/cloud/space/{space_id}` | GET |

### Modified Implementation (localtuya config_flow.py + tuya_gui.py + cloud_api.py)

| Purpose | Endpoint | HTTP Method | Where Used | Matches Original? |
|---|---|---|---|---|
| Authentication | `/v1.0/token?grant_type=1` | GET | `cloud_api.py:230` | ✅ Yes |
| Get all user devices | `/v1.0/users/{user_id}/devices` | GET | `cloud_api.py:259` | ✅ Yes |
| Get device info | `/v1.0/devices/{dev_id}` | GET | `tuya_gui.py:3835` | ✅ Yes |
| Get device specs fallback | `/v1.1/devices/{dev_id}/specifications` | GET | `tuya_gui.py:3845` | ✅ Yes |
| Get device functions | (via internal API) | GET | `cloud_api.py:async_get_device_functions` | ✅ Yes |
| Get space resources | `/v2.0/cloud/space/{space_id}/resource` | GET | `tuya_gui.py:4092`, `cloud_api.py:494` | ✅ Yes |
| Get child spaces | `/v2.0/cloud/space/child` | GET | `cloud_api.py:470` | ✅ Yes |
| Get space info | `/v2.0/cloud/space/{space_id}` | GET | tuya_gui.py (device details) | ✅ Yes |

### Endpoint Status Summary

All Tuya Cloud API endpoints used in the modified implementation match the original `hass-localtuya`
reference implementation exactly. No endpoints have been added, removed, or changed.

### LocalTuya Manual Import JSON Formats

**Format 1** (used in step 1 of manual cloud import):
```json
{
  "result": {
    "data": [
      {"res_id": "bfc0abab874dc1a864q5kn", "res_type": 0},
      {"res_id": "bf054a2177fd16678d9yds", "res_type": 0}
    ],
    "last_row_key": 2031162322342079,
    "page_size": 200
  },
  "success": true,
  "t": 1785229260540,
  "tid": "daa2e1a18a6211f19cb812e3d0098c67"
}
```

**Format 2** (used in step 2 of manual cloud import — detailed device info):
```json
{
  "result": [
    {
      "active_time": 1741388374,
      "bind_space_id": "150797786",
      "category": "tdq",
      "create_time": 1695142031,
      "custom_name": "",
      "icon": "smart/icon/ay1533257659316XGZOd/1f21cca41812827d145dc1620bf8a835.jpg",
      "id": "bfc0abab874dc1a864q5kn",
      "ip": "109.53.1.80",
      "is_online": false,
      "lat": "0",
      "local_key": "&t-ii)HEj{'W]PSq",
      "lon": "0",
      "model": "",
      "name": "1CH WiFi Switch Module 3",
      "product_id": "1o5lr0wtvu2bziz6",
      "product_name": "1CH WiFi Switch Module CB3S",
      "sub": false,
      "time_zone": "+01:00",
      "update_time": 1741388379,
      "uuid": "a1fe4be9b7581dbc"
    }
  ]
}
```

### Duplicate Detection (Three Layers)

1. **Layer 1 — unconfigured_devices filter (step 1, Format 1 path)**:
   - Excludes devices by cloud ID (`res_id`/`id`) AND MAC address
   - Only unconfigured devices pass through to step 2

2. **Layer 2 — pre-import check (step 2, Format 2 JSON path)**:
   - Before merging into `cloud_data.device_list`, each device from Format 2 JSON is checked:
     - Already-configured cloud ID → skipped
     - MAC match with any configured device → skipped (catches factory-reset devices with new cloud IDs)
   - If all devices filtered → `all_devices_configured` error shown

3. **Layer 3 — configure_device duplicate check**:
   - Per-device check during individual configuration
   - Matches by IP, cloud device ID, and MAC (including MAC from cloud data for factory-reset devices)
   - Shows `duplicate_device` error if conflict detected
