# Diagnostica Pre-Ottimizzazione — Redmi Note 9S (Xiaomi)
**Data**: 2026-08-10  
**Dispositivo**: Redmi Note 9S / Redmi / Android 12 (API 31)  
**Serial**: f5dbd3a3  

---

## 🔌 Connessione ADB
```
Device: f5dbd3a3
Status: device (autorizzato)
ADB path: /c/Programs/MinimalAdbFastboot/adb
```

---

## 📊 Stato Risorse (Baseline)

### Batteria
- **Livello**: 67%
- **Stato**: USB powered (500 mA max)
- **Temperatura**: **35.7°C** (357 decimi °C)
- **Salute**: Good (2)
- **Tensione**: 4028 mV
- **Tecnologia**: Li-poly

### Memoria (RAM + Swap)
| Metrica | Valore |
|---------|--------|
| **MemTotal** | 3,673,764 kB (~3.6 GB) |
| **MemFree** | 99,028 kB (~97 MB) |
| **MemAvailable** | 1,277,616 kB (~1.2 GB) |
| **Buffers** | 740 kB |
| **Cached** | 1,239,556 kB (~1.2 GB) |
| **SwapCached** | 8,500 kB |
| **SwapTotal** | 2,306,044 kB (~2.3 GB) |
| **SwapUsed** | ~959 MB (da `top`) |
| **SwapFree** | ~1.3 GB |

> ⚠️ **Pressione memoria evidente**: `MemFree` molto basso (97 MB), swap già al ~40% utilizzo.

### CPU (snapshot `top -b -n 1 -m 20`)
```
Tasks: 857 total, 1 running, 856 sleeping
CPU: 37% user, 27% sys, 727% idle, 7% sirq
```

**Processi chiave**:
| PID | Processo | %CPU | %MEM | Note |
|-----|----------|------|------|------|
| 1567 | `system_server` | **16.6%** | 3.0% | Normale per system_server |
| 2943 | `com.android.systemui` | 6.6% | 2.1% | System UI |
| 1141 | `surfaceflinger` | 10.0% | 0.4% | Compositor |
| 144 | `kswapd0` | **15.0%** | 0.0% | **Swap pressure ALTO** — soglia critica! |
| 17067 | `com.android.vending` | 66.5% | 2.0% | Play Store attivo (aggiornamenti?) |
| 8105 | `com.android.vending:background` | 58.9% | 1.6% | Play Store background |
| 14093 | `com.google.android.gms.persistent` | 10.3% | 1.2% | GMS persistent |
| 14856 | `com.google.android.gms` | 4.3% | 4.2% | GMS main |

---

## 🐏 Top Consumatori RAM (PSS da `dumpsys meminfo`)

| Processo (Package) | PSS (MB) | %RAM | Note |
|-------------------|----------|------|------|
| `system` (pid 1567) | 310 | 3.0% | system_server |
| `com.android.vending` (totale) | 375 | — | **Play Store + background** |
| `com.google.android.gms` (totale) | 267 | — | **GMS + persistent** |
| `com.android.systemui` | 120 | 2.1% | System UI |
| `com.miui.home` | 115 | 1.7% | **MIUI Launcher** |
| `com.miui.global.packageinstaller` | 89 | 3.3% | Installer pacchetti |
| `surfaceflinger` | 79 | 0.4% | Compositor |
| `camera.provider` | 78 | — | Camera HAL |
| `com.google.android.apps.messaging` | 73 | — | Messages |
| `com.miui.securitycenter.remote` | 34 | — | **Security Center** |
| `com.facebook.services` | 27 | — | Facebook Services |
| `com.facebook.appmanager` | 19 | — | Facebook App Manager |
| `com.xiaomi.mipicks` | 41 | — | **Mi Picks (bloatware)** |
| `com.xiaomi.mi_connect_service` | 19 | — | **Mi Connect** |
| `com.xiaomi.xmsf` | 17 | — | **Xiaomi Framework** |
| `com.miui.daemon` | 19 | — | **MIUI Daemon** |
| `com.miui.powerkeeper` | 23 | — | **Power Keeper** |
| `com.miui.guardprovider` | 23 | — | **Guard Provider** |
| `com.miui.miwallpaper` | 41 | — | **Wallpaper** |

---

## ⚙️ Configurazioni Attuali

### Pacchetti disabilitati (`pm list packages -d`)
```
package:com.android.nfc
package:com.google.android.ims
```
**Solo 2 pacchetti disabilitati** — pochissimi.

### Doze Whitelist Utente (`cmd deviceidle whitelist -user`)
```
(VUOTO — nessuna app esente da Doze)
```

### App Facebook / Social rilevate
```
package:com.facebook.services
package:com.facebook.appmanager
package:com.facebook.mlite (verificare)
package:org.telegram.messenger
package:com.sinapsi.duconnect (Ducati?)
```

### App Xiaomi / MIUI (bloatware candidato)
| Package | PSS (MB) | Funzione | Target Ottimizzazione |
|---------|----------|----------|----------------------|
| `com.xiaomi.mipicks` | 41 | Mi Picks (store) | **Disabilita** |
| `com.xiaomi.mi_connect_service` | 19 | Device connect | Disabilita se non usato |
| `com.xiaomi.xmsf` | 17 | Xiaomi Framework | Valutare |
| `com.xiaomi.account` | — | Xiaomi Account | Keep se serve sync |
| `com.xiaomi.payment` | — | Pagamenti | Keep se serve |
| `com.xiaomi.cameratools` | — | Camera tools | Keep per camera |
| `com.miui.msa.global` | — | MIUI Ads/Analytics | **Disabilita** |
| `com.miui.powerkeeper` | 23 | Battery saver | **Disabilita** (conflitta con Doze) |
| `com.miui.guardprovider` | 23 | Security | Disabilita |
| `com.miui.daemon` | 19 | System daemon | Valutare |
| `com.miui.miwallpaper` | 41 | Wallpaper | Disabilita |
| `com.miui.securityadd` | — | Security addon | Disabilita |
| `com.miui.securitycenter.remote` | 34 | Security center | **Disabilita** |
| `com.miui.global.packageinstaller` | 89 | Package installer | **NON disabilitare** (serve per installare) |

### App Google
| Package | PSS (MB) | Note |
|---------|----------|------|
| `com.google.android.gms` | 153 | Main |
| `com.google.android.gms.persistent` | 115 | Persistent |
| `com.google.android.gms.ui` | — | UI |
| `com.android.vending` | 375 | **Play Store (TOP RAM!)** |
| `com.google.android.googlequicksearchbox` | — | Google App |

### App Terze Parti (User-installed, `pm list packages -3`)
**Totale: 50+ pacchetti** — molti candidati a disabilitazione:
- `com.alibaba.aliexpresshd` (AliExpress — **RAM hog noto**)
- `com.thetileapp.tile` (Tile tracker)
- `com.skype.raider` (Skype)
- `keepass2android.keepass2android` (KeePass)
- `com.lonelycatgames.Xplore` (File manager)
- `org.telegram.messenger` (Telegram)
- `in.krosbits.musicolet` (Music player)
- `cn.wps.xiaomi.abroad.lite` (WPS Office)
- `it.Beta80Group.whereareu` (Emergenza 112)
- E molti altri...

---

## 📋 Analisi Criticità

| Criticità | Livello | Dettaglio |
|-----------|---------|-----------|
| **kswapd0 CPU 15%** | 🔴 **CRITICO** | Swap pressure alto, RAM insufficiente |
| **MemFree 97 MB** | 🔴 **CRITICO** | Quasi OOM, swap thrashing |
| **Play Store 375 MB RAM** | 🟠 **ALTO** | Vending + background = top consumer |
| **GMS totale 267 MB** | 🟠 **ALTO** | Persistent + main |
| **MIUI Bloatware ~400 MB** | 🟠 **ALTO** | mipicks, securitycenter, daemon, guard, wallpaper, powerkeeper |
| **Facebook Services** | 🟡 **MEDIO** | 27 MB + appmanager 19 MB |
| **Solo 2 pkg disabilitati** | 🟡 **MEDIO** | Ampio margine pulizia |
| **Batteria 35.7°C** | 🟢 **OK** | Temperatura normale |

---

## 🎯 Piano Ottimizzazione Proposto (Priorità)

### P1 — Critico (RAM/CPU immediati)
1. **Play Store** → Force-stop + `RUN_ANY_IN_BACKGROUND ignore` + `restricted` bucket
   - Vending + Vending:background = 375 MB + 66% CPU
2. **GMS (Google Play Services)** → Revoca `RUN_ANY_IN_BACKGROUND` + Location permissions
   - Persistent + Main = 267 MB
3. **kswapd0 15%** → Liberare RAM chiudendo processi inutili

### P2 — Alto (MIUI Bloatware — Disabilita `pm disable-user --user 0`)
| Package | RAM stimata | Comando |
|---------|-------------|---------|
| `com.xiaomi.mipicks` | 41 MB | `pm disable-user --user 0 com.xiaomi.mipicks` |
| `com.miui.securitycenter.remote` | 34 MB | `pm disable-user --user 0 com.miui.securitycenter.remote` |
| `com.miui.powerkeeper` | 23 MB | `pm disable-user --user 0 com.miui.powerkeeper` |
| `com.miui.guardprovider` | 23 MB | `pm disable-user --user 0 com.miui.guardprovider` |
| `com.miui.daemon` | 19 MB | `pm disable-user --user 0 com.miui.daemon` |
| `com.miui.miwallpaper` | 41 MB | `pm disable-user --user 0 com.miui.miwallpaper` |
| `com.miui.msa.global` | — | `pm disable-user --user 0 com.miui.msa.global` (Ads/Analytics) |

### P3 — Medio (AppOps Restrict — mantieni icona)
| Package | Azione |
|---------|--------|
| `com.android.vending` | `RUN_ANY_IN_BACKGROUND ignore` + `restricted` bucket |
| `com.google.android.gms` | `RUN_ANY_IN_BACKGROUND ignore` + Location ignore |
| `com.google.android.googlequicksearchbox` | `RUN_ANY_IN_BACKGROUND ignore` + Location ignore |
| `com.facebook.services` | `RUN_ANY_IN_BACKGROUND ignore` |
| `com.facebook.appmanager` | `RUN_ANY_IN_BACKGROUND ignore` |
| `com.xiaomi.mi_connect_service` | `RUN_ANY_IN_BACKGROUND ignore` |
| `com.xiaomi.xmsf` | `RUN_ANY_IN_BACKGROUND ignore` |

### P4 — Basso (App Terze Parti — valuta disabilitazione)
- `com.alibaba.aliexpresshd` → **Disabilita** (notorio RAM hog)
- `com.thetileapp.tile` → Disabilita se non usato
- `com.skype.raider` → Disabilita se non usato
- Valutare ogni app in `pm list packages -3` non essenziale

---

## 🔧 Comandi Verifica Rapida Post-Intervento
```bash
# CPU/RAM attuali
adb shell "COLUMNS=300 top -b -n 1 -m 15"
adb shell "ps -A -o pid,user,%cpu,%mem,cmd --sort=-%cpu | head -15"
adb shell "ps -A -o pid,user,%cpu,%mem,cmd --sort=-%mem | head -15"

# Battery
adb shell "dumpsys battery"

# Meminfo top
adb shell "dumpsys meminfo | grep -A 30 'Total PSS by process'"

# Appops check
adb shell "cmd appops get com.android.vending RUN_ANY_IN_BACKGROUND"
adb shell "cmd appops get com.google.android.gms RUN_ANY_IN_BACKGROUND"

# Doze whitelist
adb shell "cmd deviceidle whitelist -user"

# Standby bucket
adb shell "am get-standby-bucket com.android.vending"
adb shell "am get-standby-bucket com.google.android.gms"

# Pacchetti disabilitati
adb shell "pm list packages -d | wc -l"
```

---

## 📝 Note per Rollback
- `pm enable <package>` per riabilitare app disabilitate
- `cmd appops set <pkg> RUN_ANY_IN_BACKGROUND allow` per ripristinare
- `am set-standby-bucket <pkg> active` per ripristinare bucket
- Documentare ogni comando con timestamp

---

*File generato automaticamente da Hermes Agent prima dell'avvio ottimizzazione Redmi Note 9S*