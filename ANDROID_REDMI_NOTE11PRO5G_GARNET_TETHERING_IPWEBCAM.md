# Android USB Tethering & IP Webcam Analysis

**Date:** 2026-08-17
**Environment:** Home Assistant on Debian 13 (192.168.0.3) + OpenWrt Router (192.168.0.11)

---

## 📋 Executive Summary

Two Android devices are present in the network:
1. **Local device** (connected to HA server): `c9977cf0` - **2312DRA50G (garnet)** with DeviceAsWebcam
2. **Router device** (connected to OpenWrt): `69a47f6d3a61` - **Redmi Note 11 Pro 5G (veux)** - USB tethering ACTIVE, IP Webcam WORKING

---

## 🔌 Device Inventory

### Device 1: Local Android (Connected to HA Server via USB)
| Property | Value |
|----------|-------|
| **ADB Serial** | `c9977cf0` |
| **Transport** | `usb:1-10` |
| **Product** | `garnet_eea` |
| **Model** | `2312DRA50G` |
| **Device** | `garnet` |
| **Transport ID** | `5` |
| **ADB Status** | ✅ `device` (authorized) |

**Installed Camera Apps:**
- `com.android.DeviceAsWebcam` (system privileged app)
- `com.jacksoftw.webcam` (third-party)

**IP Webcam Status:**
- **NOT INSTALLED** (`com.pas.webcam` not found)
- **DeviceAsWebcam** is a system app at `/system/priv-app/DeviceAsWebcam`

**Network:** Device IP `192.168.0.159` (WiFi)
**IP Webcam Stream:** ✅ **WORKING** at `http://192.168.0.159:8080/videofeed`

---

### Device 2: Router Android (Connected to OpenWrt Router via USB) — **Redmi Note 11 Pro 5G (veux)**
| Property | Value |
|----------|-------|
| **ADB Serial** | `69a47f6d3a61` |
| **Transport** | `usb:2-1` (on router) |
| **Product** | `veux_eea` |
| **Model** | `2201116SG` / **Redmi Note 11 Pro 5G** |
| **Device** | `veux` |
| **ADB Status** | ✅ `device` (authorized) |

**IP Webcam Status:**
- ✅ **INSTALLED** (`com.pas.webcam` found)
- ✅ **STREAMING** on USB tethering interface

**USB Tethering (ACTIVE ✅):**
- Router interface: `usb0`
- Router USB IP: `10.123.72.105/24` (DHCP from phone, changes on reconnect)
- Phone IP (gateway): `10.123.72.65`
- Default route: via `usb0` metric 10

**IP Webcam Endpoints (WORKING ✅):**

*From Router (via USB tethering):*
- `http://10.123.72.65:8080/video` → HTTP 200 (MJPEG stream)
- `http://10.123.72.65:8080/videofeed` → HTTP 200 (MJPEG stream)

*From LAN (192.168.0.0/24) via WiFi:*
- `http://192.168.0.14:8080/video` → HTTP 200 (MJPEG stream) **← RECOMMENDED for Agent DVR**
- `http://192.168.0.14:8080/videofeed` → HTTP 200 (MJPEG stream) **← RECOMMENDED for Agent DVR**
- `http://192.168.0.14:8080/` → HTTP 200 (Web UI)

*Note: ONVIF (`/onvif/device_service`) is NOT enabled in IP Webcam settings — times out.*

---

## 🔗 Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                      HOME NETWORK (192.168.0.0/24)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ HA Server   │    │  Router      │    │  Android Phone   │  │
│  │ (Debian)    │◄───│  (OpenWrt)   │◄───│  Redmi Note 11   │  │
│  │ 192.168.0.3 │    │  192.168.0.11│    │  Pro 5G (veux)   │  │
│  └─────────────┘    └──────────────┘    └──────────────────┘  │
│        │                   │                    │               │
│        │            usb0  │            USB tethering           │
│        │            10.123│                    │               │
│        │            .72.105                   │               │
│        │                   ▼                    ▼               │
│        │            ┌──────────────┐    10.123.72.65           │
│        │            │   usb0       │◄─── (Phone DHCP GW)        │
│        │            │ 10.123.72.105│                            │
│        │            └──────────────┘                            │
│        │                                                        │
│        ▼                                                        │
│  ┌─────────────────┐                                           │
│  │ Local Android   │                                           │
│  │ (2312DRA50G)    │                                           │
│  │ garnet          │                                           │
│  │ 192.168.0.159   │                                           │
│  │ DeviceAsWebcam  │                                           │
│  └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Findings

### 1. **Router-Connected Phone (Redmi Note 11 Pro 5G / veux) — FULLY OPERATIONAL**
- ✅ **ADB Authorized**: `69a47f6d3a61 device usb:2-1`
- ✅ **USB Tethering Active**: `usb0` interface up with IP `10.16.159.174/24`
- ✅ **IP Webcam Installed**: `com.pas.webcam` package present
- ✅ **IP Webcam Streaming**: 
  - `http://10.16.159.126:8080/video` → HTTP 200
  - `http://10.16.159.126:8080/videofeed` → HTTP 200
- ✅ **Ready for Agent DVR**

### 2. **Local Android (2312DRA50G / garnet) — Alternative Camera Source**
- ✅ **IP Webcam Active**: Working at `http://192.168.0.159:8080/videofeed`
- ✅ **DeviceAsWebcam**: System privileged app available
- ✅ **Network**: Connected via WiFi (192.168.0.159)
- ✅ **ADB**: Authorized and accessible locally (`c9977cf0`)

---

## 🛠️ Setup Commands Used

### Authorize ADB on Router Phone
```bash
# On Redmi Note 11 Pro 5G (connected to router via USB):
# 1. Unlock phone → Notification shade → "USB charging" → "File transfer" (MTP)
# 2. Accept "Allow USB debugging?" popup → "Always allow from this computer"

# Verify on router:
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router devices -l"
# Shows: 69a47f6d3a61 device usb:2-1 product:veux_eea model:2201116SG device:veux
```

### Enable USB Tethering
```bash
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/enable_usb_tether.sh"
# Output: OK: USB Tethering interface active!

# Verify:
ssh -i /home/carlo/router_key root@192.168.0.11 "ip -br addr show dev usb0"
# usb0: 10.16.159.174/24
```

### Verify IP Webcam on Router Phone
```bash
# Check package installed:
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router -s 69a47f6d3a61 shell 'pm list packages | grep -i webcam'"
# package:com.pas.webcam

# Test stream from router (USB tethering):
ssh -i /home/carlo/router_key root@192.168.0.11 "curl -I http://10.123.72.65:8080/video"
# HTTP 200 OK, Server: IP Webcam Server 0.4

# Test stream from LAN (WiFi) - RECOMMENDED for Agent DVR:
curl -I http://192.168.0.14:8080/video
# HTTP 200 OK, Server: IP Webcam Server 0.4
```

---

## 📡 SSH Access Commands

### Router SSH (OpenWrt)
```bash
# Primary connection
ssh -i /home/carlo/docker/homeassistant/config/.ssh/router_key \
    -o StrictHostKeyChecking=no \
    root@192.168.0.11

# Quick command execution
ssh -i /home/carlo/docker/homeassistant/config/.ssh/router_key \
    -o StrictHostKeyChecking=no \
    root@192.168.0.11 "your_command_here"
```

### ADB via Router
```bash
# Check devices
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router devices -l"

# Shell access to router phone
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router -s 69a47f6d3a61 shell 'your_command'"

# Install APK
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router install /path/to/app.apk"
```

---

## 🔍 DeviceAsWebcam Analysis (Local Device - garnet)

The local device (`c9977cf0` - 2312DRA50G / garnet) has **`com.android.DeviceAsWebcam`** which is:
- **System privileged app** (UID 1000, `android.uid.system`)
- **Located at**: `/system/priv-app/DeviceAsWebcam`
- **Receives**: `android.hardware.usb.action.USB_STATE` broadcasts
- **Purpose**: Android 12+ DeviceAsWebcam feature for USB webcam functionality

**Not IP Webcam** - this is a different system component.

---

## 📊 Current Stream Status

| Source | URL | Status |
|--------|-----|--------|
| **Router Phone (LAN WiFi)** | `http://192.168.0.14:8080/video` | ✅ **WORKING** (HTTP 200, MJPEG) **← RECOMMENDED** |
| **Router Phone (LAN WiFi)** | `http://192.168.0.14:8080/videofeed` | ✅ **WORKING** (HTTP 200, MJPEG) **← RECOMMENDED** |
| **Router Phone (USB tethering)** | `http://10.123.72.65:8080/video` | ✅ WORKING (HTTP 200, MJPEG) — router only |
| **Router Phone (USB tethering)** | `http://10.123.72.65:8080/videofeed` | ✅ WORKING (HTTP 200, MJPEG) — router only |
| **Local Device (WiFi)** | `http://192.168.0.159:8080/videofeed` | ✅ **WORKING** (HTTP 200, MJPEG) |

---

## 🎬 Agent DVR Configuration

### For Router Phone (Redmi Note 11 Pro 5G / veux) — RECOMMENDED (via LAN WiFi)
```
Camera Type: IP Camera
URL: http://192.168.0.14:8080/videofeed
Stream Type: MJPEG
Resolution: 1920x1080 (or phone's front camera max)
FPS: 30
Authentication: None
```

*Alternative (router-only access via USB tethering):*
```
Camera Type: IP Camera
URL: http://10.123.72.65:8080/videofeed
Stream Type: MJPEG
Resolution: 1920x1080
FPS: 30
Authentication: None
```

### For Local Device (2312DRA50G / garnet) — ALTERNATIVE
```
Camera Type: IP Camera
URL: http://192.168.0.159:8080/videofeed
Stream Type: MJPEG
Resolution: 1920x1080
FPS: 30
Authentication: None
```

---

## ✅ Completed Checklist

- [x] **Authorize ADB** on router-connected Redmi Note 11 Pro 5G
- [x] **Enable USB Tethering** via `enable_usb_tether.sh`
- [x] **Verify IP Webcam installed** on router phone (`com.pas.webcam`)
- [x] **Test IP Webcam stream** on USB tethering interface (10.123.72.65:8080)
- [x] **Verify local device stream** (192.168.0.159:8080/videofeed)
- [x] **Add pre-flight check** in `usb_tether_ha.sh` for intranet mode - validates USB tethering availability before attempting activation
- [x] **Fix dashboard error message display** - automation preserves error messages instead of clearing them
- [ ] **Configure Agent DVR** with stream URL
- [ ] **Test continuous streaming** stability

---

## 🐛 Fixed Issues

### **Intranet Mode Activation Failure (Fixed Aug 17, 2026)**

**Problem:** When activating "intranet" mode from Home Assistant, the system would:
1. Return `{"state":"activating","mode":"intranet","message":"Attivazione in corso..."}` immediately
2. Run the activation in background (`nohup setsid ... &`)
3. Later fail silently with `"ERRORE: Attivazione Intranet fallita"` in logs
4. Dashboard showed misleading "attivazione modalità intranet in corso..." because automation cleared message on state change

**Root Cause:** The `activate_debian()` function in `usb_tether_ha.sh` ran the tethering activation as a background job, returning `rc=0` immediately even when no USB tethering device was connected to Debian. The phone (Redmi Note 11 Pro 5G / `veux`) is connected to the **router**, not to Debian.

**Fix Applied:** Two-part fix:

**1. Pre-flight check with persistent error marker** in `/config/helpers/usb_tether_ha.sh`:
- Added `ERROR_MARKER` file (`/config/logs/usb_tether/last_error.marker`)
- Pre-flight check runs `detect` command on target host before activation
- On failure: writes error message + timestamp to marker, returns `error` state
- On success: clears marker
- `run_status()` checks marker first and returns `error` state if present

```bash
# PRE-FLIGHT CHECK in activate_debian() and activate_windows()
local detect_out
detect_out="$(ssh_debian \"sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh detect\" 2>&1)"
local detect_rc=$?
if (( detect_rc != 0 )) || [[ -z "$detect_out" ]]; then
    # Write error marker for sensor to pick up
    printf '%s\n%s\n' "Tethering USB non disponibile su Debian: collega il telefono e attiva il tethering USB prima di procedere" "$(date '+%Y-%m-%d %H:%M:%S')" > "$ERROR_MARKER"
    json_error "Tethering USB non disponibile su Debian: collega il telefono e attiva il tethering USB prima di procedere"
    return 0
fi
# Clear error marker on success
rm -f "$ERROR_MARKER" 2>/dev/null || true
```

**2. Automation fix** in `/config/packages/usb_tether.yaml` - preserves error messages:
```yaml
# usb_tether_aggiorna_messaggio - NON pulisce se il messaggio contiene "ERRORE"
- choose:
    - conditions:
        - condition: template
          value_template: "{{ 'ERRORE' in states('input_text.usb_tether_status_message') }}"
      sequence: []
    - conditions: []
      sequence:
        - action: input_text.set_value
          target:
            entity_id: input_text.usb_tether_status_message
          data:
            value: ""
```

**Result:** Now when attempting intranet mode without a phone connected to the target host:
```json
{"state":"error","mode":"intranet","message":"Tethering USB non disponibile su Debian: collega il telefono e attiva il tethering USB prima di procedere"}
```
Sensor returns error state with timestamp:
```json
{"state":"error","mode":"server","message":"Tethering USB non disponibile su Debian... (pre-flight fallito alle 2026-08-17 14:44:24)"}
```
Dashboard shows **actual error** instead of misleading "attivazione in corso..."

---

## 🐛 MIUI USB Function Switching Bug

**Problem:** `svc usb setFunctions rndis,adb` crashes with:
```
java.io.FileNotFoundException: /data/system/theme_config/theme_compatibility.xml: open failed: ENOENT
```
This is a **MIUI theme framework bug** on Redmi Note 11 Pro 5G — the `svc usb` command triggers system resource loading that fails on a missing theme config file, preventing USB function switching.

**Attempts failed:**
- `svc usb setFunctions rndis,adb` → crash (theme_compatibility.xml)
- `setprop sys.usb.config rndis,adb` → "Failed to set property" (read-only property in MIUI)
- Direct sysfs writes (`/sys/class/android_usb/android0/functions`) → Permission denied (non-root)
- `su` not available (production build, no root)

**Workaround:** Set USB tethering manually via phone Settings → Developer Options → USB Usb configuration → "USB tethering"

---

## 📝 Notes

1. **Two different phones** - `garnet` (2312DRA50G) local vs `veux` (Redmi Note 11 Pro 5G) on router
2. **Router phone USB tethering** - Active when enabled manually via phone UI (MIUI bug blocks remote activation)
3. **Phone IP changes on reconnect** - DHCP from phone assigns new IP in 10.x.x.x range (currently 10.123.72.0/24)
4. **Local device has working stream too** - can be used as backup camera source
5. **Router ADB wrapper** - `/usr/bin/adb_router` is MIPS-compiled ADB with RAM-loaded libraries
6. **IP Webcam endpoints** - both `/video` and `/videofeed` work on router phone
7. **Pre-flight check implemented** - intranet mode validates USB tethering availability before attempting activation
8. **Dashboard error display fixed** - automation no longer clears error messages on state change
9. **ADB key fix applied** - `export HOME=/root` added to both `/etc/hotplug.d/usb/99-usb-tethering` and `/usr/bin/enable_usb_tether.sh` to ensure consistent ADB key usage
10. **ADB authorization persists** via WiFi (192.168.0.14:5555) when "Always allow" is checked — only USB re-enumeration requires re-accepting the dialog