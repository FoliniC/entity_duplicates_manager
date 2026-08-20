# Android USB Tethering & IP Webcam Analysis

**Date:** 2026-08-19 (last updated)
**Environment:** Home Assistant on Debian 13 (192.168.0.3) + OpenWrt Router (192.168.0.11)

---

## 📋 Executive Summary

Two Android devices are present in the network:
1. **Local device** (connected to HA server): `c9977cf0` - **2312DRA50G (garnet)** with DeviceAsWebcam
2. **Router device** (connected to OpenWrt): `69a47f6d3a61` - **Redmi Note 11 Pro 5G (veux)** - USB tethering ACTIVE, IP Webcam WORKING

**Current deployment (Aug 19, 2026):** The router phone (`veux`) has been moved to the HA server (Debian) for direct management via USB and WiFi ADB. All services (IP Webcam, scrcpy) now run via WiFi LAN (`192.168.0.14`).

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

> **Note:** `2312DRA50G` is a **Redmi Note 11 Pro 5G** (model name `garnet`, codename garnet_eea).
> Verified via `adb shell getprop`: `ro.product.device=garnet`, `ro.product.model=2312DRA50G`.

---

### Device 2: Router Android (Connected to OpenWrt Router via USB) — **Redmi Note 11 Pro 5G (veux)**

| Property | Value |
|----------|-------|
| **ADB Serial** | `69a47f6d3a61` |
| **Transport** | `usb:2-1` (on router) / `usb:1-9` (on Debian HA) |
| **Product** | `veux_eea` |
| **Model** | `2201116SG` / **Redmi Note 11 Pro 5G** |
| **Device** | `veux` |
| **ADB Status** | ✅ `device` (authorized) |

> **Note:** This is a **different phone** from the local device. While local is `garnet`/`2312DRA50G`,
> the router phone is `veux`/`2201116SG` (both are Redmi Note 11 Pro 5G but different regional variants/codenames).
> Verified via `adb_router shell getprop`:
> `ro.product.device=veux`, `ro.product.model=2201116SG`, `ro.product.name=veux_eea`.

**IP Webcam Status:**
- ✅ **INSTALLED** (`com.pas.webcam` found)
- ✅ **STREAMING** on WiFi LAN (`192.168.0.14:8080`)

**USB Tethering (ACTIVE ✅ when enabled manually):**
- Router interface: `usb0`
- Router USB IP: `10.16.159.174/24` (DHCP from phone, changes on reconnect)
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

> **IP variability note:** The phone assigns IPs via DHCP over the `usb0` tethering link; both the phone gateway IP
> and the router's USB IP change on USB re-enumeration. The current values shown above are a snapshot. Always probe
> with `ip -br addr show dev usb0` and `ip route` on the router for the live addresses.

---

## 🎯 Key Findings

### 1. **Router-Connected Phone (Redmi Note 11 Pro 5G / veux) — FULLY OPERATIONAL**
- ✅ **ADB Authorized**: `69a47f6d3a61 device usb:2-1` (router) / `usb:1-9` (Debian)
- ✅ **USB Tethering Active**: `usb0` interface up with IP `10.16.159.174/24` (when manually enabled)
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
- [x] **Move phone to HA server** for direct USB + WiFi ADB management
- [x] **Install scrcpy 4.1** from GitHub releases
- [x] **Enable ADB over WiFi** (port 5555) via USB
- [x] **Activate IP Webcam** via ADB + manual UI
- [x] **Disable TeamViewer** (unwanted background processes)
- [x] **Optimize scrcpy** for LAN (8M bitrate, max-size 1080, 30 FPS)
- [x] **Validate scrcpy production config** (60fps, 20M, H.264 HW encoder, --ignore-video-encoder-constraints, max-size 1080)
- [x] **Verify resource cleanup** on scrcpy exit
- [ ] **Configure Agent DVR** with stream URL
- [ ] **Test continuous streaming** stability
- [ ] **Apply manual phone optimizations** (IP Webcam FPS 15, Audio off, Battery "No restrictions")

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

## 🆕 scrcpy 4.1 Deployment (Aug 19, 2026)

### Installation
```bash
# Download from GitHub releases
cd /tmp
wget https://github.com/Genymobile/scrcpy/releases/download/v4.1/scrcpy-linux-x86_64-v4.1.tar.gz
tar -xzf scrcpy-linux-x86_64-v4.1.tar.gz
sudo cp scrcpy-linux-x86_64-v4.1/scrcpy /usr/local/bin/scrcpy
sudo cp scrcpy-linux-x86_64-v4.1/scrcpy-server /usr/local/bin/scrcpy-server
sudo chmod +x /usr/local/bin/scrcpy /usr/local/bin/scrcpy-server

# Verify
scrcpy --version
# scrcpy 4.1
# SDL: 3.4.12, libavcodec: 62.28.102, libusb: 1.0.30
```

### ADB over WiFi Setup (via USB)
```bash
# Enable TCP mode on phone via USB
adb -s 69a47f6d3a61 tcpip 5555
# restarting in TCP mode port: 5555

# Connect via WiFi
adb connect 192.168.0.14:5555
# connected to 192.168.0.14:5555

# Verify
adb devices -l
# 69a47f6d3a61           device usb:1-9 ...
# 192.168.0.14:5555      device product:veux_eea model:2201116SG device:veux ...
```

### Optimized scrcpy Commands (LAN) — **VALIDATED Aug 19, 2026**

**Production — Maximum Responsiveness (60fps, H.264 HW encoder, low latency):**
```bash
scrcpy -s 192.168.0.14:5555 \
  --max-fps 60 \
  --video-bit-rate 20M \
  --max-size 1080 \
  --video-codec h264 \
  --ignore-video-encoder-constraints \
  --stay-awake \
  --turn-screen-off
```
*Tested: 60fps, 20Mbps, H.264 HW encoder (media.hwcodec 30% CPU), exit code 0, clean resource release.*

**Standard (balanced quality/performance, 30fps):**
```bash
scrcpy -s 192.168.0.14:5555 --max-fps 30 --video-bit-rate 8M --max-size 1080 --stay-awake
```

**Headless / control only (screen off, saves battery):**
```bash
scrcpy -s 192.168.0.14:5555 --max-fps 60 --video-bit-rate 20M --max-size 1080 --video-codec h264 --ignore-video-encoder-constraints --stay-awake --turn-screen-off
```

**With audio (Opus 128k):**
```bash
scrcpy -s 192.168.0.14:5555 --max-fps 30 --video-bit-rate 8M --max-size 1080 --audio-bit-rate 128K --audio-codec opus --stay-awake
```

### Key scrcpy 4.1 Flag Changes

| Old flag (v3.x) | New flag (v4.1+) |
|-----------------|------------------|
| `--bit-rate` | `--video-bit-rate` / `-b` |
| `--max-fps` | `--max-fps` (unchanged) |
| `--stay-awake` | `--stay-awake` / `-w` (unchanged) |
| `--turn-screen-off` | `--turn-screen-off` / `-S` (unchanged) |
| N/A | `--max-size` (critical for 1080x2400 displays) |

### Why `--max-size 1080` is Required
The phone's native resolution (1080x2400) causes `java.lang.IllegalArgumentException: null` encoder error at high bitrates. Limiting to 1080p height resolves this.

---

## 🆕 IP Webcam Activation via ADB (Aug 19, 2026)

### Activity Resolution
```bash
# Find launcher activity
adb -s 192.168.0.14:5555 shell 'cmd package resolve-activity -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.pas.webcam'
# Result: com.pas.webcam.Configuration

# Launch
adb -s 192.168.0.14:5555 shell 'am start -n com.pas.webcam/com.pas.webcam.Configuration'
```

### Manual Step Required
The IP Webcam app **requires manual "Start server" tap** in the UI after launching the activity. The ADB launch opens the config screen; user must tap the play button.

### Verified Endpoints
```bash
curl -I http://192.168.0.14:8080/videofeed  # HTTP 200
curl -I http://192.168.0.14:8080/video      # HTTP 200
```

---

## 🆕 TeamViewer Disabling (Aug 19, 2026)

### Problem
TeamViewer Host (`com.teamviewer.host.market`) and QuickSupport addon (`com.teamviewer.quicksupport.addon.universal`) were running but:
- No "Don't ask again" checkbox appeared on connection popup
- Connection required manual acceptance every time
- Background processes consumed resources

### Solution: Disable via ADB
```bash
# Force stop
adb -s 192.168.0.14:5555 shell 'am force-stop com.teamviewer.host.market'
adb -s 192.168.0.14:5555 shell 'am force-stop com.teamviewer.quicksupport.addon.universal'

# Disable for current user (persists across reboots)
adb -s 192.168.0.14:5555 shell 'pm disable-user com.teamviewer.host.market'
adb -s 192.168.0.14:5555 shell 'pm disable-user com.teamviewer.quicksupport.addon.universal'

# Verify
adb -s 192.168.0.14:5555 shell 'ps -A | grep -iE "teamviewer|host"'
# (no output = success)
```

### Why Not "Auto-accept"?
TeamViewer's "auto-accept" (LAN confirmation) requires the user to **manually check "Don't ask again" on first connection popup**. This cannot be set via ADB/settings — it's stored in encrypted `shared_prefs` only writable by the app UI. Since scrcpy provides full LAN control with lower latency, TeamViewer is unnecessary.

---

## 🆕 CPU / Memory Optimization Analysis (Aug 19, 2026)

### Baseline (before optimization)
| Process | CPU% | RAM% |
|---------|------|------|
| cameraserver | 127% | 2.5% |
| IP Webcam | 48% | 6.1% |
| scrcpy (16M) | 24% | 2.5% |
| mediacodec | 17-24% | 0.1-0.3% |

### After scrcpy Optimization (8M + max-size 1080)
| Process | CPU% | RAM% |
|---------|------|------|
| cameraserver | 130% | 2.5% |
| IP Webcam | 50% | 6.3% |
| **scrcpy (8M)** | **30%** | **2.8%** |
| mediacodec | 23-26% | 0.1-0.3% |

### System Specs
- **RAM**: 5.5 GB total, 2.2 GB available (40%)
- **Swap**: 4 GB (2.8 GB free)
- **Storage**: 102 GB (76 GB free)
- **CPU**: 8 cores (6× efficiency @ 1.8 GHz, 2× performance @ 2.2 GHz)
- **Governor**: `schedutil` (cannot change to `performance` without root)
- **Battery**: 100%, 32.9°C

### Applied Optimizations (no root required)
```bash
# Device idle whitelist (prevents Doze mode kill)
adb shell 'cmd deviceidle whitelist +com.pas.webcam'
adb shell 'cmd deviceidle whitelist +com.genymobile.scrcpy'

# Disable animations (reduces system_server CPU)
settings put global window_animation_scale 0
settings put global transition_animation_scale 0
settings put global animator_duration_scale 0

# Stay awake while plugged
settings put global stay_on_while_plugged_in 3

# AppOps for background stability
cmd appops set com.pas.webcam RUN_IN_BACKGROUND allow
cmd appops set com.pas.webcam RUN_ANY_IN_BACKGROUND allow
```

### Pending Manual Optimizations (on phone)
| Action | Path | Impact |
|--------|------|--------|
| IP Webcam FPS: 30 → 15 | Settings → Video → Max FPS: 15 | -30% CPU IP Webcam |
| IP Webcam Audio: Off | Settings → Audio → Disable audio | -Wake lock, -CPU audio |
| Battery Saver: No restrictions | Settings → Battery → App battery saver → IP Webcam / scrcpy → No restrictions | Background stability |

---

## 🆕 Resource Cleanup Verification (Aug 19, 2026)

After closing scrcpy window on Debian:

| Resource | Status | Verification |
|----------|--------|--------------|
| scrcpy processes | ✅ Zero | `ps -A \| grep -i scrcpy` → none |
| Wake locks | ✅ Zero | `dumpsys power \| grep -i scrcpy` → none |
| TCP port 27183 | ✅ Closed | `cat /proc/net/tcp \| grep 6A27` → none |
| Android services | ✅ Zero | `dumpsys activity services \| grep -i scrcpy` → none |
| CPU/Memory | ✅ Baseline | `top \| grep scrcpy` → only grep process |

**Conclusion:** scrcpy 4.1 cleans up **all resources** on exit — no orphaned processes, wake locks, or sockets.

---

## 📝 Notes

1. **Two different phones** - `garnet` (2312DRA50G) local vs `veux` (2201116SG, Redmi Note 11 Pro 5G) on router
2. **Router phone USB tethering** - Active when enabled manually via phone UI (MIUI bug blocks remote activation via `svc usb`)
3. **Phone IP changes on reconnect** - DHCP from phone assigns new IP in 10.x.x.x range (currently 10.123.72.0/24)
4. **Local device has working stream too** - can be used as backup camera source
5. **Router ADB wrapper** - `/usr/bin/adb_router` is a MIPS-compiled ADB with RAM-loaded libraries
6. **IP Webcam endpoints** - both `/video` and `/videofeed` work on router phone
7. **Pre-flight check implemented** - intranet mode validates USB tethering availability before attempting activation
8. **Dashboard error display fixed** - automation no longer clears error messages on state change
9. **ADB key fix applied** - `export HOME=/root` added to both `/etc/hotplug.d/usb/99-usb-tethering` and `/usr/bin/enable_usb_tether.sh` to ensure consistent ADB key usage
10. **ADB authorization persists** via WiFi (192.168.0.14:5555) when "Always allow" is checked — only USB re-enumeration requires re-accepting the dialog
11. **scrcpy 4.1 deployed** - installed from GitHub releases, optimized for LAN (8M, max-size 1080)
12. **ADB over WiFi active** - `192.168.0.14:5555` stable, survives USB disconnect
13. **TeamViewer disabled** - `pm disable-user` on both packages, no background processes
14. **IP Webcam active on WiFi** - `192.168.0.14:8080/videofeed` HTTP 200
15. **Resource cleanup verified** - scrcpy exits cleanly, no residual resources

---

## 📋 Quick Reference — Production Commands

```bash
# === IP WEBCAM (Frigate/Agent DVR) ===
http://192.168.0.14:8080/videofeed

# === SCRCPY REMOTE CONTROL ===
# Standard
scrcpy -s 192.168.0.14:5555 --max-fps 30 --video-bit-rate 8M --max-size 1080 --stay-awake

# Headless (screen off)
scrcpy -s 192.168.0.14:5555 --max-fps 30 --video-bit-rate 8M --max-size 1080 --stay-awake --turn-screen-off

# With audio
scrcpy -s 192.168.0.14:5555 --max-fps 30 --video-bit-rate 8M --max-size 1080 --audio-bit-rate 128K --audio-codec opus --stay-awake

# === ADB ===
adb devices -l                                    # List devices
adb connect 192.168.0.14:5555                     # Connect WiFi ADB
adb -s 192.168.0.14:5555 shell 'pm disable-user com.teamviewer.host.market'  # Disable TeamViewer

# === ROUTER USB TETHERING ===
ssh -i /home/carlo/docker/homeassistant/config/.ssh/router_key root@192.168.0.11 "/usr/bin/enable_usb_tether.sh"
ssh -i /home/carlo/docker/homeassistant/config/.ssh/router_key root@192.168.0.11 "ip -br addr show dev usb0"

# === MANUAL PHONE SETTINGS ===
# 1. USB Tethering: Settings → Developer Options → USB Configuration → "USB tethering"
# 2. IP Webcam FPS: 15, Audio: Off
# 3. Battery: No restrictions for IP Webcam & scrcpy
```