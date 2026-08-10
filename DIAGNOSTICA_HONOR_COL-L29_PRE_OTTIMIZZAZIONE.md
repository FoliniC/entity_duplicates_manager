# Diagnostica Pre-Ottimizzazione — HONOR COL-L29
**Data**: 2026-08-09  
**Dispositivo**: HONOR COL-L29 (Android 10, API 29, kirin970)  
**NOTA**: Dispositivo DIVERSO dal Xiaomi Redmi Note 13 Pro 5G (HyperOS) descritto in `OTTIMIZZAZIONE_TELEFONO.md`

---

## 🔌 Connessione ADB
```
Device: UEEDU18712002254
Status: device (autorizzato)
ADB path: /c/Programs/MinimalAdbFastboot/adb
```

---

## 📊 Stato Risorse (Baseline)

### Batteria
- **Livello**: 61%
- **Stato**: USB powered (500 mA max)
- **Temperatura**: 32.0°C (320 decimi °C)
- **Salute**: Good (2)
- **Tensione**: 4020 mV
- **Tecnologia**: Li-poly

### Memoria (RAM + Swap)
| Metrica | Valore |
|---------|--------|
| **MemTotal** | 3,714,672 kB (~3.5 GB) |
| **MemFree** | 135,412 kB (~132 MB) |
| **MemAvailable** | 1,457,600 kB (~1.4 GB) |
| **Buffers** | 3,772 kB |
| **Cached** | 1,478,084 kB (~1.4 GB) |
| **SwapTotal** | 2,162,684 kB (~2.1 GB) |
| **SwapUsed** | ~1.1 GB (stimato da `top`) |
| **SwapFree** | ~0.9 GB |

> ⚠️ **Pressione memoria evidente**: `MemFree` molto basso (132 MB), swap già al ~50% utilizzo.

### CPU (snapshot `top -b -n 1 -m 25`)
```
Tasks: 643 total, 1 running, 642 sleeping
CPU: 16% user, 3% nice, 44% sys, 734% idle, 3% sirq
```

**Processi chiave**:
| PID | Processo | %CPU | %MEM | Note |
|-----|----------|------|------|------|
| 169 | `kswapd0` | **4.7%** | 0.0% | **Swap pressure** — soglia >10% critica, ma 4.7% già attivo |
| 5087 | `android.process.media` | **38.8%** | 1.2% | **Media scanner attivo** — probabile loop indicizzazione |
| 1472 | `system_server` | 17.9% | 6.4% | Normale per system_server |
| 2564 | `com.google.android.gms.persistent` | 4.6% | 3.4% | Google Play Services |
| 15809 | `com.huawei.hwid.core` | 4.1% | 3.7% | Huawei ID core |
| 7036 | `com.huawei.appmarket` | 3.2% | 1.8% | AppGallery Huawei |
| 3988 | `com.google.android.gms` | 2.6% | 3.0% | Google Play Services main |
| 1828 | `com.android.systemui` | 1.8% | 3.0% | System UI |

---

## 🐏 Top Consumatori RAM (PSS da `dumpsys meminfo`)

| Processo (Package) | PSS (MB) | %RAM | Note |
|-------------------|----------|------|------|
| `system` (pid 1472) | 221 | 6.4% | system_server |
| `android.hardware.graphics.allocator@2.0-service` | 136 | — | Graphics allocator |
| `com.android.systemui` | 124 | 3.0% | System UI |
| `com.google.android.gms.ui` | 121 | — | Google Play UI |
| `com.google.android.youtube` | 121 | — | YouTube |
| `com.google.android.googlequicksearchbox:googleapp` | 121 | — | Google App (search) |
| `com.google.android.googlequicksearchbox:search` | 83 | — | Google Search |
| `com.google.android.googlequicksearchbox:interactor` | 57 | — | Google Interactor |
| **Totale Google App/QuickSearch** | **~261** | **~7%** | Somma processi Google |
| `com.huawei.search` | 102 | — | Huawei Search |
| `com.android.settings` | 101 | 4.0% | Impostazioni (attiva?) |
| `com.google.android.gms.persistent` | 96 | 3.4% | GMS persistent |
| `com.google.android.gms` | 89 | 3.0% | GMS main |
| `com.huawei.android.launcher` | 79 | — | Huawei Launcher |
| `com.huawei.hwid.core` | 78 | 3.7% | Huawei ID Core |
| **com.whatsapp** | **72** | **2.0%** | **WhatsApp** |
| **com.xiaomi.wearable** (totale 2 processi) | **~88** | **~2.5%** | **Xiaomi Wearable** |
| `com.google.android.apps.photos` | 60 | 1.9% | Google Photos |
| `com.android.gallery3d` | 58 | 0.7% | Gallery |
| `com.huawei.appmarket` | 52 | 1.8% | AppGallery |
| `com.huawei.hwid` | 39 | — | Huawei ID |
| `com.huawei.vassistant` | 31 | 1.1% | Huawei Voice Assistant |

---

## ⚙️ Configurazioni Attuali

### Pacchetti disabilitati (`pm list packages -d`)
```
package:com.huawei.autoinstallapkfrommcc
package:com.google.android.ims
```
**Solo 2 pacchetti disabilitati** — molto pochi rispetto al documento Xiaomi.

### Doze Whitelist Utente (`cmd deviceidle whitelist -user`)
```
(VUOTO — nessuna app esente da Doze)
```

### App Facebook / Social rilevate
```
package:com.facebook.services
package:com.whatsapp
```
*Nota: `com.facebook.katana` (app principale) NON installata; solo `services`.*

### App Xiaomi rilevate
```
package:com.xiaomi.wearable
package:com.xiaomi.wearable:device (processo separato)
```

### App Huawei principali (bloatware candidato)
```
com.huawei.appmarket           (AppGallery) — 52 MB RAM, 3.2% CPU
com.huawei.hwid.core           (Huawei ID) — 78 MB RAM, 4.1% CPU
com.huawei.hwid                — 39 MB RAM
com.huawei.hwid.persistent     — 12 MB RAM
com.huawei.hwid.container2/3   — ~34 MB RAM cadauno
com.huawei.search              — 102 MB RAM
com.huawei.iaware              — 24 MB RAM (AI/optimization)
com.huawei.vassistant          — 31 MB RAM, 1.1% CPU (Voice Assistant)
com.huawei.hitouch             — 10 MB RAM (Touch service)
com.huawei.intelliServer       — 7 MB RAM
com.huawei.hiai.engineservice  — 8 MB RAM (AI Engine)
com.huawei.recsys              — 9 MB RAM (Recommendation system)
```

---

## 📋 Differenze Chiave vs Documento Xiaomi (OTTIMIZZAZIONE_TELEFONO.md)

| Aspetto | Documento (Xiaomi Note 13 Pro 5G) | Reale (HONOR COL-L29) | Impatto |
|---------|-----------------------------------|----------------------|---------|
| **RAM fisica** | 11.3 GB | **3.5 GB** | Meno margine, swap critico |
| **Swap** | 2.5 GB (2.5 GB usata) | 2.1 GB (~1.1 GB usata) | Swap già 50% pieno |
| **OS** | HyperOS | Android 10 (EMUI/Magic UI) | Comandi `pm disable` diversi |
| **kswapd0 CPU** | Monitorare >10% | **4.7% baseline** | Già sotto pressione |
| **Motorola IoV** | 44% CPU (TOP) | **Assente** | N/A |
| **AliExpress** | 530+ MB RAM | **Assente** | N/A |
| **Mi Picks** | App sistema 78 MB | **Assente** | N/A |
| **Xiaomi AI Engine** | `com.xiaomi.aicr` | **Assente** | N/A |
| **Xiaomi Wearable** | Non menzionato | **Presente (88 MB)** | Nuovo target |
| **WhatsApp** | 156 mAh bg | **72 MB RAM, 0% CPU** | Già in Doze? |
| **Facebook** | App + Services | **Solo Services** | Meno invasivo |
| **Google Play Services** | 19.5% CPU | 4.6% + 2.6% CPU | Migliore |

---

## 🎯 Piano Ottimizzazione Proposto (Priorità)

### P1 — Critico (CPU/RAM immediati)
1. **`android.process.media` (38.8% CPU)** → Force-stop + `RUN_IN_BACKGROUND ignore`
2. **`kswapd0` al 4.7%** → Liberare RAM chiudendo processi inutili per ridurre swap pressure

### P2 — Alto (RAM persistente)
3. **`com.xiaomi.wearable` (88 MB RAM)** → Freeze se non usato (`pm disable-user --user 0` + appops)
4. **`com.whatsapp` (72 MB RAM)** → `RUN_ANY_IN_BACKGROUND ignore` + `restricted` bucket se notifiche non critiche
5. **Google App/QuickSearch tot ~261 MB** → Revoca `RUN_ANY_IN_BACKGROUND` + Location permissions

### P3 — Medio (Huawei bloatware)
6. **`com.huawei.appmarket`** (52 MB, 3.2% CPU) → Restrict background
7. **`com.huawei.hwid.*` cluster** (~160 MB totali) → Valutare disable se non serve Huawei ID
8. **`com.huawei.vassistant` / `hitouch` / `iaware` / `hiai`** → AI/voice services, restrict se non usati

### P4 — Google Play Services (come documento)
9. Revoca `COARSE_LOCATION`, `FINE_LOCATION`, `RUN_ANY_IN_BACKGROUND` per `com.google.android.gms` e `com.google.android.googlequicksearchbox`

---

## 🔧 Comandi Verifica Rapida Post-Intervento
```bash
# CPU/RAM
adb shell "COLUMNS=300 top -b -n 1 -m 20"
adb shell "ps -A -o pid,user,%cpu,%mem,cmd --sort=-%cpu | head -15"
adb shell "ps -A -o pid,user,%cpu,%mem,cmd --sort=-%mem | head -15"

# Battery
adb shell "dumpsys battery"

# Meminfo top
adb shell "dumpsys meminfo | grep -A 30 'Total PSS by process'"

# Appops check
adb shell "cmd appops get com.whatsapp RUN_ANY_IN_BACKGROUND"
adb shell "cmd appops get com.xiaomi.wearable RUN_ANY_IN_BACKGROUND"

# Doze whitelist
adb shell "cmd deviceidle whitelist -user"

# Standby bucket
adb shell "am get-standby-bucket com.whatsapp"
adb shell "am get-standby-bucket com.xiaomi.wearable"
```

---

## 📝 Note per Rollback
- Tutti gli interventi usano `appops set ... ignore` + `am set-standby-bucket restricted` (reversibili con `allow` + `active`)
- `pm disable-user --user 0` per freeze app (reversibile con `pm enable`)
- Nessun comando richiede root o modifica partizioni di sistema
- Documentare ogni comando eseguito con timestamp per eventuale rollback selettivo

---

*File generato automaticamente da Hermes Agent prima dell'avvio ottimizzazione*