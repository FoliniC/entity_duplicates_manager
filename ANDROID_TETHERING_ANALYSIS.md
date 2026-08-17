# Android USB Tethering & IP Webcam Analysis

**Date:** 2026-08-16
**Environment:** Home Assistant on Debian 13 (192.168.0.3) + OpenWrt Router (192.168.0.11)

---

## 📋 Executive Summary

Two Android devices are present in the network:
1. **Local device** (connected to HA server): `c9977cf0` - 2312DRA50G with DeviceAsWebcam
2. **Router device** (connected to OpenWrt): `69a47f6d3a61` - Redmi Note 11 Pro 5G (unauthorized ADB)

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

---

### Device 2: Router Android (Connected to OpenWrt Router via USB)
| Property | Value |
|----------|-------|
| **ADB Serial** | `69a47f6d3a61` |
| **Transport** | `usb:2-1` (on router) |
| **Product** | `garnet_eea` |
| **Model** | `2312DRA50G` / Redmi Note 11 Pro 5G |
| **Device** | `garnet` |
| **ADB Status** | ❌ `unauthorized` |

**IP Webcam Status:**
- **NOT INSTALLED** on router-connected device
- **ADB unauthorized** - requires physical acceptance on phone screen

**USB Tethering:**
- Active on router interface `usb0`
- Phone IP: `10.187.189.252` (DHCP from phone)
- Router USB IP: `10.187.189.24/24`
- Gateway: `10.187.189.252`

---

## 🔗 Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                      HOME NETWORK (192.168.0.0/24)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ HA Server   │    │  Router      │    │  Android Phone   │  │
│  │ (Debian)    │◄───│  (OpenWrt)   │◄───│  (Redmi Note 11  │  │
│  │ 192.168.0.3 │    │  192.168.0.11│    │   Pro 5G)        │  │
│  └─────────────┘    └──────────────┘    └──────────────────┘  │
│        │                   │                    │               │
│        │            usb0  │            USB tethering           │
│        │            10.187│                    │               │
│        │            .189.24│                   │               │
│        │                   ▼                    ▼               │
│        │            ┌──────────────┐    10.187.189.252          │
│        │            │   usb0       │◄─── (Phone DHCP GW)        │
│        │            │ 10.187.189.24│                            │
│        │            └──────────────┘                            │
│        │                                                        │
│        ▼                                                        │
│  ┌─────────────────┐                                           │
│  │ Local Android   │                                           │
│  │ (2312DRA50G)    │                                           │
│  │ 192.168.0.159   │                                           │
│  │ DeviceAsWebcam  │                                           │
│  └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Findings

### 1. **Router-Connected Phone (Target for Tethering)**
- **ADB Unauthorized**: Phone shows `unauthorized` in router's ADB
- **Requires**: Physical acceptance of "Allow USB debugging?" on phone screen
- **IP Webcam**: Not installed on this device
- **USB Functions**: Currently in tethering mode (RNDIS active)

### 2. **Local Android (Alternative Camera Source)**
- **IP Webcam Active**: Working at `http://192.168.0.159:8080/videofeed`
- **DeviceAsWebcam**: System privileged app available
- **Network**: Connected via WiFi (192.168.0.159)
- **ADB**: Authorized and accessible locally

---

## 🛠️ Required Actions

### Priority 1: Authorize Router ADB
**On the Redmi Note 11 Pro 5G (connected to router):**
1. Unlock phone screen
2. Pull down notification shade
3. Tap "USB charging this device" / "Carica questo dispositivo via USB"
4. Select **"File transfer" / "Trasferimento file" (MTP)**
5. Accept **"Allow USB debugging?" / "Consenti debug USB?"** popup
6. Check **"Always allow from this computer"**

**Verify on router:**
```bash
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router devices -l"
# Should show: 69a47f6d3a61 device usb:2-1
```

### Priority 2: Install IP Webcam on Router Phone
Once ADB authorized:
```bash
# From router:
ssh -i /home/carlo/router_key root@192.168.0.11 "
    /usr/bin/adb_router shell 'curl -o /tmp/IPWebcam.apk https://github.com/ishankhare07/IPWebcam/releases/download/1.26.0/IPWebcam-1.26.0.apk'
    /usr/bin/adb_router install /tmp/IPWebcam.apk
"

# Grant permissions:
ssh -i /home/carlo/router_key root@192.168.0.11 "
    /usr/bin/adb_router shell 'pm grant com.pas.webcam android.permission.CAMERA'
    /usr/bin/adb_router shell 'pm grant com.pas.webcam android.permission.WRITE_EXTERNAL_STORAGE'
    /usr/bin/adb_router shell 'pm grant com.pas.webcam android.permission.RECORD_AUDIO'
"

# Start IP Webcam:
ssh -i /home/carlo/router_key root@192.168.0.11 "
    /usr/bin/adb_router shell 'am start -n com.pas.webcam/com.pas.webcam.MainActivity'
"
```

### Priority 3: Verify Stream Access
From HA server (Debian 192.168.0.3):
```bash
# Test stream via router network
curl -I http://10.187.189.252:8080/video

# Or if phone uses different port
curl -I http://10.187.189.252:8080/videofeed
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

# Shell access
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router shell 'your_command'"

# Install APK
ssh -i /home/carlo/router_key root@192.168.0.11 "/usr/bin/adb_router install /path/to/app.apk"
```

---

## 🔍 DeviceAsWebcam Analysis (Local Device)

The local device (`c9977cf0`) has **`com.android.DeviceAsWebcam`** which is:
- **System privileged app** (UID 1000, `android.uid.system`)
- **Located at**: `/system/priv-app/DeviceAsWebcam`
- **Receives**: `android.hardware.usb.action.USB_STATE` broadcasts
- **Purpose**: Likely for USB webcam functionality (Android 12+ DeviceAsWebcam feature)

**Not IP Webcam** - this is a different system component.

---

## 📊 Current Stream Status

| Source | URL | Status |
|--------|-----|--------|
| Local Device (WiFi) | `http://192.168.0.159:8080/videofeed` | ✅ **WORKING** (HTTP 200) |
| Router Phone (USB) | `http://10.187.189.252:8080/video` | ❌ Not tested (IP Webcam not installed) |
| Router Phone (USB) | `http://10.187.189.252:8080/videofeed` | ❌ Not tested (IP Webcam not installed) |

---

## 🎬 Next Steps Checklist

- [ ] **Authorize ADB** on router-connected Redmi Note 11 Pro 5G
- [ ] **Install IP Webcam** on router-connected phone
- [ ] **Grant permissions** (CAMERA, STORAGE, RECORD_AUDIO)
- [ ] **Start IP Webcam** service
- [ ] **Verify stream** accessible from HA server via router network
- [ ] **Configure Agent DVR** with stream URL
- [ ] **Test continuous streaming** stability

---

## 📝 Notes

1. **Two different phones** - don't confuse the local 2312DRA50G with the router-connected Redmi Note 11 Pro 5G
2. **USB tethering active** - router has `usb0` interface with phone as gateway
3. **ADB authorization required** - physical interaction needed on phone
4. **Local device has working camera stream** - can be used as alternative if router phone setup fails
5. **Router ADB wrapper** - `/usr/bin/adb_router` is a MIPS-compiled ADB with RAM-loaded libraries