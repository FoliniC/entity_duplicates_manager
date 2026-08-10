# Ottimizzazione Post-Intervento — HONOR COL-L29 come IP Camera RTSP
**Data**: 2026-08-09  
**Obiettivo**: Dispositivo dedicato solo a streaming RTSP via app "IP Webcam" (`com.pas.webcam`)  
**App camera attive**: `com.pas.webcam` (IP Webcam), `com.dev47apps.droidcam` (DroidCam - backup), `com.huawei.camera` (system)

---

## 📊 Stato Finale Post-Ottimizzazione

### Batteria
- **Livello**: 65% (+4% durante ottimizzazione)
- **Temperatura**: **31.0°C** (↓ da 32.0°C iniziale)
- **Stato**: USB powered, charging

### Memoria (RAM + Swap)
| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| **MemFree** | 135 MB | ~79 MB | -56 MB (app camera attiva) |
| **MemAvailable** | 1.4 GB | ~1.3 GB | Stabile |
| **Swap Used** | ~1.1 GB | **749 MB** | **↓ ~350 MB** ✅ |
| **Swap Free** | ~0.9 GB | **1.4 GB** | **↑ ~500 MB** ✅ |

### CPU (snapshot `top`)
- **kswapd0**: Non più in top-20 (era 4.7%) → **Pressione swap risolta** ✅
- **android.process.media**: Non più in top-20 (era 38.8%) → **Media scanner fermato** ✅
- **system_server**: 14-18% (normale)
- **com.pas.webcam**: 0% CPU, **125 MB RAM** (attiva, in attesa configurazione RTSP)

---

## 🔧 Interventi Eseguiti

### 1. Processi Sistema Problematici
```bash
# Media scanner (consumava 38.8% CPU)
am force-stop android.process.media

# Google Play Services / Google App - background + location revocati
cmd appops set com.google.android.gms RUN_ANY_IN_BACKGROUND ignore
cmd appops set com.google.android.gms RUN_IN_BACKGROUND ignore
cmd appops set com.google.android.gms COARSE_LOCATION ignore
cmd appops set com.google.android.gms FINE_LOCATION ignore

cmd appops set com.google.android.googlequicksearchbox RUN_ANY_IN_BACKGROUND ignore
cmd appops set com.google.android.googlequicksearchbox RUN_IN_BACKGROUND ignore
cmd appops set com.google.android.googlequicksearchbox COARSE_LOCATION ignore
cmd appops set com.google.android.googlequicksearchbox FINE_LOCATION ignore
```

### 2. App Non Necessarie — **DISABILITATE** (`pm disable-user --user 0`)

#### Huawei Bloatware (18 pacchetti)
| Pacchetto | Funzione | RAM risparmiata (stima) |
|-----------|----------|------------------------|
| `com.huawei.appmarket` | AppGallery | 52 MB |
| `com.huawei.search` | Huawei Search | 102 MB |
| `com.huawei.vassistant` | Voice Assistant | 31 MB |
| `com.huawei.hitouch` | Touch service | 10 MB |
| `com.huawei.iaware` | AI Optimization | 24 MB |
| `com.huawei.hiai` | AI Engine | 8 MB |
| `com.huawei.recsys` | Recommendation | 9 MB |
| `com.huawei.intelliServer.intelliServer` | Intelli Server | ~7 MB |
| `com.huawei.intelligent` | Intelligent service | ~5 MB |
| `com.huawei.nearby` | Nearby sharing | ~5 MB |
| `com.huawei.wallet` | Wallet | ~5 MB |
| `com.huawei.parentcontrol` | Parental control | ~3 MB |
| `com.huawei.numberidentity` | Caller ID | ~3 MB |
| `com.huawei.hifolder` | Folder app | ~3 MB |
| `com.huawei.hwid` | Huawei ID | 39 MB |

#### Google Apps Non Essenziali (22 pacchetti)
`com.google.android.apps.docs*`, `gmail`, `maps`, `youtube music`, `calendar`, `keep`, `messaging`, `translate`, `bard`, `photos` (lasciato attivo per backup?), `music`, `tachyon` (Meet), ecc.

#### App Terze Parti Inutili (23 pacchetti)
Amazon, Booking, Microsoft OneDrive, Adobe Reader, Opera, Avira, Mi apps (Xiaomi), Tuya SmartLife, speedtest, weather apps, X-plore, Tenda router, radio apps, games, ecc.

#### Social/Comunicazione
- `com.facebook.services` (disabilitato)
- `com.whatsapp` → **AppOps restrict** (non disabilitato per possibili notifiche)
- `com.xiaomi.wearable` → **AppOps restrict + standby rare** (88 MB risparmiati)

---

## 📦 Pacchetti Disabilitati Totali: **63**

### Mantenuti ATTIVI (Essenziali per IP Camera RTSP)
| Pacchetto | Motivo |
|-----------|--------|
| `com.pas.webcam` | **IP Webcam - APP PRINCIPALE RTSP** |
| `com.dev47apps.droidcam` | Backup DroidCam |
| `com.huawei.camera` | System camera (hardware access) |
| `com.huawei.camerakit.impl` | Camera framework |
| `com.google.android.gms` | Play Services (base, limitato background) |
| `com.android.vending` | Play Store (per aggiornamenti app camera) |
| `com.huawei.android.launcher` | Launcher (accesso UI configurazione) |
| `com.android.settings` | Impostazioni (config rete, debug) |
| `com.android.systemui` | System UI |

---

## ⚠️ Configurazione RTSP Pendente

L'app **`com.pas.webcam` (IP Webcam)** è avviata ma **non espone ancora porte RTSP/HTTP**.

**Porte tipiche IP Webcam**:
- **HTTP/MJPEG**: 8080
- **RTSP**: 554 (o 8554 se non root)
- **RTMP**: 1935
- **HTTPS**: 443 / 8443

### Prossimi Passi Richiesti (MANUALI sul device)
1. **Sblocca schermo** → apri app **"IP Webcam"** (icona videocamera verde)
2. **Configura**:
   - `Connection settings` → `Local streaming` → **Enable**
   - `Port` → **8080** (HTTP) / **8554** (RTSP)
   - `Video preferences` → Risoluzione, FPS, bitrate
   - `Audio` → Enable/Disable per RTSP
   - `Startup` → `Start on boot` ✅, `Run in background` ✅
3. **Avvia server** → pulsante "Start server" in basso
4. **Verifica**: `rtsp://<IP_DEL_TELEFONO>:8554/video` o `http://<IP>:8080/video`

### Comando Verifica Porte (dopo configurazione)
```bash
adb shell "cat /proc/net/tcp | awk '\$2 ~ /:1F90|:2170|:7A4/ {print}'"
# 1F90=8080, 2170=8554, 7A4=1956 (altre porte comuni)
```

---

## 🔄 Rollback Selettivo (Se Necessario)

### Riabilitare App Singola
```bash
adb shell "pm enable com.huawei.appmarket"
adb shell "pm enable com.google.android.apps.maps"
# ecc.
```

### Ripristinare AppOps Google
```bash
adb shell "cmd appops set com.google.android.gms RUN_ANY_IN_BACKGROUND allow"
adb shell "cmd appops set com.google.android.gms COARSE_LOCATION allow"
adb shell "cmd appops set com.google.android.gms FINE_LOCATION allow"
```

### Ripristinare WhatsApp / Xiaomi Wearable
```bash
adb shell "cmd appops set com.whatsapp RUN_ANY_IN_BACKGROUND allow"
adb shell "am set-standby-bucket com.whatsapp active"
adb shell "cmd appops set com.xiaomi.wearable RUN_ANY_IN_BACKGROUND allow"
adb shell "am set-standby-bucket com.xiaomi.wearable active"
```

---

## 📈 Risultati Attesi per Uso IP Camera 24/7

| Metrica | Target |
|---------|--------|
| **RAM libera stabile** | > 200 MB (vs 135 MB iniziale) |
| **Swap usage** | < 500 MB (vs 1.1 GB iniziale) |
| **kswapd0 CPU** | < 1% (vs 4.7% iniziale) |
| **Temperatura** | < 35°C caricabatterie collegato |
| **Battery drain** | Minimo (solo camera + WiFi + sistema base) |
| **Uptime** | Giorni senza riavvio |

---

*Ottimizzazione completata. Dispositivo pronto per configurazione manuale RTSP su app IP Webcam.*