# Android USB Tethering & IP Webcam Analysis

**Date:** 2026-08-16
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
- Router USB IP: `10.16.159.174/24`
- Phone IP (gateway): `10.16.159.126`
- Default route: via `usb0` metric 10

**IP Webcam Endpoints (WORKING ✅):**
- `http://10.16.159.126:8080/video` → HTTP 200 (MJPEG stream)
- `http://10.16.159.126:8080/videofeed` → HTTP 200 (MJPEG stream)

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
│        │            10.16 │                    │               │
│        │            .159.174                   │               │
│        │                   ▼                    ▼               │
│        │            ┌──────────────┐    10.16.159.126           │
│        │            │   usb0       │◄─── (Phone DHCP GW)        │
│        │            │ 10.16.159.174│                            │
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

# Test stream from router:
ssh -i /home/carlo/router_key root@192.168.0.11 "curl -I http://10.16.159.126:8080/video"
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
| **Router Phone (USB tethering)** | `http://10.16.159.126:8080/video` | ✅ **WORKING** (HTTP 200, MJPEG) |
| **Router Phone (USB tethering)** | `http://10.16.159.126:8080/videofeed` | ✅ **WORKING** (HTTP 200, MJPEG) |
| **Local Device (WiFi)** | `http://192.168.0.159:8080/videofeed` | ✅ **WORKING** (HTTP 200, MJPEG) |

---

## 🎬 Agent DVR Configuration

### For Router Phone (Redmi Note 11 Pro 5G / veux) — RECOMMENDED
```
Camera Type: IP Camera
URL: http://10.16.159.126:8080/video
Stream Type: MJPEG
Resolution: 1920x1080 (or phone's front camera max)
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
- [x] **Test IP Webcam stream** on USB tethering interface (10.16.159.126:8080)
- [x] **Verify local device stream** (192.168.0.159:8080/videofeed)
- [ ] **Configure Agent DVR** with stream URL
- [ ] **Test continuous streaming** stability

---

## 📝 Notes

1. **Two different phones** - `garnet` (2312DRA50G) local vs `veux` (Redmi Note 11 Pro 5G) on router
2. **Router phone fully operational** - USB tethering + IP Webcam both working
3. **Phone IP changes on reconnect** - DHCP from phone assigns new IP in 10.x.x.x range
4. **Local device has working stream too** - can be used as backup camera source
5. **Router ADB wrapper** - `/usr/bin/adb_router` is MIPS-compiled ADB with RAM-loaded libraries
6. **IP Webcam endpoints** - both `/video` and `/videofeed` work on router phone