# Controllo e Ottimizzazione Telefono (Xiaomi Redmi Note 13 Pro 5G - HyperOS)

Questo documento descrive le procedure diagnostiche e di ottimizzazione delle risorse per lo smartphone Xiaomi tramite ADB (Android Debug Bridge).

---

## 🔌 Preparazione e Connessione ADB

La suite ADB è scaricata localmente all'interno della cartella scratch di Antigravity:
*   **Path ADB**: `/home/carlo/.gemini/antigravity/brain/460ac445-8d6c-4746-86b2-27f169bf3966/scratch/platform-tools/adb`

### Verifica Dispositivi Collegati
Per verificare che il telefono sia connesso e autorizzato:
```bash
/home/carlo/.gemini/antigravity/brain/460ac445-8d6c-4746-86b2-27f169bf3966/scratch/platform-tools/adb devices
```
*Se compare `unauthorized`, sbloccare lo schermo del telefono e accettare la richiesta di debug RSA.*

---

## 📊 Comandi di Diagnostica Rapida

### 1. Monitoraggio CPU in tempo reale (senza troncamento nomi)
```bash
/home/carlo/.gemini/antigravity/brain/460ac445-8d6c-4746-86b2-27f169bf3966/scratch/platform-tools/adb shell "COLUMNS=300 top -b -n 1 -m 25"
```
*Nota: Monitorare in particolare la percentuale di CPU di `[kswapd0]` (se > 10%, la RAM è satura e il sistema sta spendendo CPU per comprimere la memoria in ZRAM).*

### 2. Monitoraggio RAM (Total PSS per processo)
Per identificare quali applicazioni occupano più memoria RAM fisica:
```bash
/home/carlo/.gemini/antigravity/brain/460ac445-8d6c-4746-86b2-27f169bf3966/scratch/platform-tools/adb shell "dumpsys meminfo" | grep -A 30 "Total PSS by process"
```

### 3. Profilatore di CPU (Script Python Dedicato)
Per calcolare la media dell'uso CPU su un arco temporale di 10 secondi ed evitare falsi positivi dovuti a picchi momentanei:
```bash
python3 /home/carlo/.gemini/antigravity/brain/460ac445-8d6c-4746-86b2-27f169bf3966/scratch/check_cpu.py
```

### 4. Stato Batteria e Temperatura
```bash
/home/carlo/.gemini/antigravity/brain/460ac445-8d6c-4746-86b2-27f169bf3966/scratch/platform-tools/adb shell "dumpsys battery"
```
*Nota: La temperatura è espressa in decimi di grado (es. `336` significa 33.6°C).*

---

## ⚡ Ottimizzazione e Risoluzione Problemi

### 1. Terminare App in Background Consumatrici di RAM
Se la RAM è satura e `kswapd0` consuma troppa CPU, forzare la chiusura delle app inattive di terze parti:
```bash
# Sostituire con il percorso dell'ADB locale
alias adb_local="/home/carlo/.gemini/antigravity/brain/460ac445-8d6c-4746-86b2-27f169bf3966/scratch/platform-tools/adb"

# AliExpress (Solitamente il peggior consumatore di RAM in background, > 800MB)
adb_local shell am force-stop com.alibaba.aliexpresshd

# Social
adb_local shell am force-stop com.facebook.katana
adb_local shell am force-stop com.instagram.android

# Altri Servizi non critici
adb_local shell am force-stop com.apkpure.aegon
adb_local shell am force-stop com.airasia.mobile
adb_local shell am force-stop com.fusionmedia.investing
adb_local shell am force-stop com.weward
```

### 2. Gestione Xiaomi AI Engine (`com.xiaomi.aicr`)
Se il servizio AI di sistema consuma stabilmente molta CPU (oltre il 50%) drenando la batteria:

*   **Opzione 1 (Meno invasiva - Consigliata)**: Attendere 2-3 giorni dopo un aggiornamento di sistema HyperOS (l'engine esegue indicizzazione e compilazione in background automatica).
*   **Opzione 2 (Disattivazione temporanea)**:
    ```bash
    adb_local shell pm disable-user --user 0 com.xiaomi.aicr
    ```
*   **Opzione 3 (Riattivazione del servizio)**:
    ```bash
    adb_local shell pm enable com.xiaomi.aicr
    ```

### 3. Congelamento / Disattivazione App di Terze Parti (Freeze)
È possibile disattivare un'app per impedirne completamente l'esecuzione in background senza doverla disinstallare. L'app non comparirà più nel launcher e non consumerà risorse.

#### Elenco App Congelate e Ripristino:

*   **My Data Manager** (`com.mobidia.android.mdm`)
    *   *Congela*: `adb_local shell pm disable-user --user 0 com.mobidia.android.mdm`
    *   *Scongela*: `adb_local shell pm enable com.mobidia.android.mdm`

*   **Intesa Sanpaolo (La Tua Banca)** (`com.latuabancaperandroid`)
    *   *Congela*: `adb_local shell pm disable-user --user 0 com.latuabancaperandroid`
    *   *Scongela*: `adb_local shell pm enable com.latuabancaperandroid`

*   **Microsoft Launcher** (`com.microsoft.launcher`)
    *   *Congela*: `adb_local shell pm disable-user --user 0 com.microsoft.launcher`
    *   *Scongela*: `adb_local shell pm enable com.microsoft.launcher`

### 4. Restrizione Rigida in Background (Senza nascondere l'app)
Se vuoi continuare a usare un'app normalmente (mantenendo l'icona visibile), ma vuoi impedire in modo assoluto che esegua codice o consumi RAM/CPU in background quando non è aperta sullo schermo:

#### Elenco App Limitate in Background:
*   **AliExpress** (`com.alibaba.aliexpresshd`)
*   **Google Chrome** (`com.android.chrome`)
*   **WeWard** (`com.weward`)
*   **Facebook** (`com.facebook.katana`)
*   **Podbean** (`com.podbean.app.podcast`)
*   **MG iSmart** (`com.saicmotor.iov.europe`)
*   **3BMeteo** (`com.Meteosolutions.Meteo3b`)
*   **OKOK International** (`com.chipsea.btcontrol.en`)

#### Modello comandi per limitare un'app (es. `<PACKAGE>`):
```bash
# AppOps: Blocca esecuzione in background
adb_local shell cmd appops set <PACKAGE> RUN_IN_BACKGROUND ignore
adb_local shell cmd appops set <PACKAGE> RUN_ANY_IN_BACKGROUND ignore

# Standby Bucket: Forza lo stato Restricted
adb_local shell am set-standby-bucket <PACKAGE> restricted

# Termina la sessione corrente
adb_local shell am force-stop <PACKAGE>
```

#### Modello comandi per ripristinare lo stato normale (es. `<PACKAGE>`):
```bash
# AppOps: Consenti esecuzione in background
adb_local shell cmd appops set <PACKAGE> RUN_IN_BACKGROUND allow
adb_local shell cmd appops set <PACKAGE> RUN_ANY_IN_BACKGROUND allow

# Standby Bucket: Ripristina lo stato Active
adb_local shell am set-standby-bucket <PACKAGE> active
```

---

## 📅 Sessione Ottimizzazione - 2026-07-31

### Stato iniziale
- **Batteria**: 15% (in carica USB 500mA)
- **RAM**: 11.3 GB totali, 99.4% usata (63 MB liberi), Swap 2.5 GB
- **CPU**: Google Play Services 19.5%, system_server 17.1%, Motorola IoV 44.3% (nuovo)
- **Temperatura**: 33.5°C → 30.7°C (post ottimizzazione)

---

### Interventi eseguiti (ordinati per impatto)

#### 1. Motorola IoV Europe (`com.saicmotor.iov.europe`) - **TOP CONSUMER 44% CPU**
```bash
adb_local shell am force-stop com.saicmotor.iov.europe
adb_local shell cmd appops set com.saicmotor.iov.europe RUN_ANY_IN_BACKGROUND ignore
```
**Risultato**: Eliminato 44% CPU, liberati ~500 MB RAM. Servizio per connessione auto Motorola.

#### 2. App pesanti terminate + background revocato
| App | Package | RAM liberata | Azioni |
|-----|---------|--------------|--------|
| Retouch | `com.xt.retouchoversea` | 458 MB | force-stop + `RUN_ANY_IN_BACKGROUND ignore` |
| Investing | `com.fusionmedia.investing` | 289 MB | force-stop + `RUN_ANY_IN_BACKGROUND ignore` |
| Adobe Reader | `com.adobe.reader` | 235 MB | force-stop |
| iLovePDF | `com.ilovepdf.www` | 202 MB | force-stop |
| AliExpress | `com.alibaba.aliexpresshd` | 530 MB (multi-processo) | force-stop tutti i processi |
| Microsoft Suite | Outlook, Bing, OfficeHub, OneDrive, EMMX | ~1 GB | force-stop 5 processi principali |

#### 3. Facebook (`com.facebook.katana`) - Limitazione aggressiva
```bash
# AppOps
adb_local shell cmd appops set com.facebook.katana RUN_ANY_IN_BACKGROUND ignore
adb_local shell cmd appops set com.facebook.katana WAKE_LOCK ignore

# Doze whitelist
adb_local shell cmd deviceidle whitelist -user -com.facebook.katana

# Force-stop
adb_local shell am force-stop com.facebook.katana
adb_local shell am force-stop com.facebook.services
```
**Nota**: Servizi foreground (`HeroKeepAliveService`, `PreloadedFbnsService`) riavviano l'app. Configurato MacroDroid per force-stop periodico ogni 30 min (solo schermo spento).

#### 4. Xiaomi Mi Picks (`com.xiaomi.mipicks`) - App di sistema
```bash
adb_local shell am force-stop com.xiaomi.mipicks
adb_local shell cmd appops set com.xiaomi.mipicks RUN_ANY_IN_BACKGROUND ignore
adb_local shell cmd deviceidle whitelist -user -com.xiaomi.mipicks
```
**Nota**: Non disabilitabile (`pm disable-user` fallisce). Riavviata automaticamente ma ora limitata.

#### 5. Revoca permessi Location + Background
| App | Permessi revocati |
|-----|-------------------|
| **Google Play Services** (`com.google.android.gms`) | `COARSE_LOCATION`, `FINE_LOCATION`, `GPS`, `MONITOR_LOCATION`, `MONITOR_HIGH_POWER_LOCATION`, `FINE_LOCATION_SOURCE` + `RUN_ANY_IN_BACKGROUND ignore` |
| **Google App** (`com.google.android.googlequicksearchbox`) | `COARSE_LOCATION`, `FINE_LOCATION`, `GPS`, `MONITOR_LOCATION`, `MONITOR_HIGH_POWER_LOCATION`, `RUN_ANY_IN_BACKGROUND ignore` |
| **Instagram** (`com.instagram.android`) | `RUN_ANY_IN_BACKGROUND ignore` (location già `ignore`) |
| **Facebook** | `RUN_ANY_IN_BACKGROUND ignore`, `WAKE_LOCK ignore` |
| **KeePass2Android** (`keepass2android.keepass2android`) | `RUN_ANY_IN_BACKGROUND ignore` |
| **Xiaomi Wearable** (`com.xiaomi.wearable`) | `COARSE_LOCATION`, `FINE_LOCATION`, `GPS`, `MONITOR_LOCATION`, `MONITOR_HIGH_POWER_LOCATION`, `RUN_ANY_IN_BACKGROUND ignore` + **whitelist Doze rimossa** |
| **AndroidFuel** (`org.vernazza.androidfuel`) | Tutti location + `RUN_ANY_IN_BACKGROUND ignore` |
| **LTE Discovery** (`net.simplyadvanced.ltediscovery`) | `RUN_ANY_IN_BACKGROUND ignore` + force-stop |
| **Fake GPS** (`com.lexa.fakegps`) | **Whitelist Doze rimossa** |

#### 6. Whitelist Doze Utente - Pulizia
```bash
# Rimosse (non bypassano più Doze):
adb_local shell cmd deviceidle whitelist -user -com.lexa.fakegps
adb_local shell cmd deviceidle whitelist -user -com.xiaomi.wearable
adb_local shell cmd deviceidle whitelist -user -com.facebook.katana
adb_local shell cmd deviceidle whitelist -user -com.xiaomi.mipicks

# Ancora attive (valutare rimozione):
# com.whatsapp, de.komoot.android, io.homeassistant.companion.android, com.thetileapp.tile
```

#### 7. Tentativo disabilitazione servizi Google Play Services (falliti - richiedono root)
```bash
# Nearby Presence
adb_local shell pm disable-user --user 0 com.google.android.gms/com.google.android.gms.nearby.presence.service.LifeCycleService
# Play Integrity
adb_local shell pm disable-user --user 0 com.google.android.gms/com.google.android.gms.play.integrity.api.service.IntegrityApiPersistentService
# Facebook HeroKeepAliveService
adb_local shell pm disable-user --user 0 com.facebook.katana/com.facebook.video.heroplayer.service.HeroKeepAliveService
```
**Tutti falliti con `SecurityException: Shell cannot change component state`**

---

### Stato finale (post-ottimizzazione)

| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| **RAM usata** | ~10.8 GB (96%) | ~9.5 GB (84%) | **↓ ~1.3 GB** |
| **Top app RAM** | Retouch 458 MB | system_server 725 MB | Sistema |
| **CPU Motorola IoV** | **44.3%** | 0% | ✅ Eliminato |
| **CPU Facebook** | 4.2% | 3.5% | ↓ (ma riavviato da FG service) |
| **Batteria** | 15% | 60% | 🔋 In carica |
| **Temperatura** | 33.5°C | 30.7°C | ↓ 2.8°C |
| **Swap** | 2.5 GB | ~1.5 GB | ↓ |

## �� 📅 Sessione Ottimizzazione - 2026-08-11

### Stato iniziale (pre-ottimizzazione)
- **Batteria**: 90% (in carica USB 500mA)
- **RAM**: 11.2 GB totali, 99.5% usata (62 MB liberi), Swap 4.8 GB
- **CPU**: Motorola IoV 1.0 GB RAM (top), Microsoft AppManager 126%, WeWard 53%
- **Temperatura**: 32.9°C
- **kswapd0**: 3.3% CPU (pressione memoria)

### Interventi eseguiti (ordinati per impatto)

#### 1. Motorola IoV Europe (`com.saicmotor.iov.europe`) - **TOP CONSUMER 1 GB RAM**
```bash
adb_local shell am force-stop com.saicmotor.iov.europe
adb_local shell cmd appops set com.saicmotor.iov.europe RUN_ANY_IN_BACKGROUND ignore
adb_local shell am set-standby-bucket com.saicmotor.iov.europe restricted
```
**Risultato**: Eliminato 1 GB RAM, processo terminato.

#### 2. Microsoft AppManager
```bash
adb_local shell am force-stop com.microsoft.appmanager
adb_local shell cmd appops set com.microsoft.appmanager RUN_ANY_IN_BACKGROUND ignore
adb_local shell am set-standby-bucket com.microsoft.appmanager restricted
```
**Risultato**: CPU 126% → 2%, RAM 434 MB → 157 MB.

#### 3. WeWard
```bash
adb_local shell am force-stop com.weward
adb_local shell cmd appops set com.weward RUN_ANY_IN_BACKGROUND ignore
adb_local shell am set-standby-bucket com.weward restricted
```
**Risultato**: CPU 53% → 0%, processo terminato.

#### 4. App pesanti terminate + background revocato
| App | Package | RAM liberata | Azioni |
|-----|---------|--------------|--------|
| Facebook | `com.facebook.katana` | force-stop | AppOps RUN_ANY_IN_BACKGROUND ignore |
| Instagram | `com.instagram.android` | force-stop | AppOps RUN_ANY_IN_BACKGROUND ignore |
| AliExpress | `com.alibaba.aliexpresshd` | force-stop tutti i processi | AppOps RUN_ANY_IN_BACKGROUND ignore |
| Investing | `com.fusionmedia.investing` | force-stop | AppOps RUN_ANY_IN_BACKGROUND ignore |
| APKPure | `com.apkpure.aegon` | force-stop | AppOps RUN_ANY_IN_BACKGROUND ignore |
| Tile | `com.thetileapp.tile` | force-stop | AppOps RUN_ANY_IN_BACKGROUND ignore |
| Twitter/X | `com.twitter.android` | force-stop | AppOps RUN_ANY_IN_BACKGROUND ignore |

#### 5. Whitelist Doze Utente - Pulizia completata
```bash
adb_local shell cmd deviceidle whitelist -user
# Risultato: lista vuota (tutte le eccezioni rimosse)
```

### Stato finale (post-ottimizzazione)

| Metrica | Prima | Dopo | Δ |
|---------|-------|------|---|
| **RAM usata** | ~11.2 GB (99.5%) | ~10.8 GB (93.5%) | ������ ��↓ ~400 MB |
| **RAM libera** | 62 MB | 425 MB | ������ ��↑ 363 MB |
| **MemAvailable** | ~500 MB | 4.9 GB | ������ ��↑ 4.4 GB |
| **Swap usato** | 4.8 GB | 3.15 GB | ������ ��↓ 1.65 GB |
| **Swap libero** | 7.5 GB | 9.1 GB | ������ ��↑ 1.6 GB |
| **Motorola IoV** | 1.0 GB RAM attivo | Terminato | ��� � � ✅ Eliminato |
| **Microsoft AppManager** | 126% CPU, 434 MB | 2% CPU, 157 MB | ��� � � ✅ Limitato |
| **WeWard** | 53% CPU, 420 MB | 0% CPU | ��� � � ✅ Terminato |
| **kswapd0 CPU** | 3.3% | 0% (non in top) | ��� � � ✅ Pressione alleviata |
| **Batteria** | 90% | 93% | ���� �� �� 🔋 In carica |
| **Temperatura** | 32.9°C | 31.8°C | ���� �� �� 🟢 ������ ��↓ 1.1°C |
| **Processi totali** | 927 | 881 | ���� �� �� 🟢 ������ ��↓ 46 |


---\n\n### Prossimi interventi consigliati\n
1. **WhatsApp** - 156 mAh CPU bg + radio mobile bg → `RUN_ANY_IN_BACKGROUND ignore` + whitelist remove
2. **Tile** (`com.thetileapp.tile`) - 201 MB RAM, whitelist attiva → rimuovi se non usato
3. **Komoot** (`de.komoot.android`) - 255 MB RAM, whitelist attiva → rimuovi se non tracci GPS
4. **Mi Security Center Remote** - 607 MB RAM (app sistema) → valutare disabilitazione avvio auto
5. **MacroDroid** - Configurato per force-stop Facebook ogni 30 min (schermo spento)

---

### Comandi di verifica rapida
```bash
# CPU/RAM attuali
adb_local shell ps -A -o pid,user,%cpu,%mem,cmd --sort=-%cpu | head -20
adb_local shell ps -A -o pid,user,%cpu,%mem,cmd --sort=-%mem | head -20

# Battery stats app chiave
adb_local shell "dumpsys batterystats --charged 2>/dev/null | grep 'UID u0a' | grep -E '294|416|368|498|372|322|148'"

# Whitelist Doze utente
adb_local shell cmd deviceidle whitelist -user

# Verifica appops Facebook
adb_local shell cmd appops get com.facebook.katana RUN_ANY_IN_BACKGROUND
adb_local shell cmd appops get com.facebook.katana WAKE_LOCK
```


## ���� �� �� 📅 Aggiornamento 2026-08-11 (dopo utilizzo)

Dopo alcune ore di utilizzo, ecco lo stato attuale:

- **Motorola IoV**: terminato, nessun processo attivo, AppOps ignore, bucket RESTRICTED (50)
- **WeWard**: terminato, nessun processo attivo, AppOps ignore, bucket RESTRICTED (50)
- **Microsoft AppManager**: ancora in bucket WORKING_SET (5) nonostante tentativi di impostarlo a RESTRICTED, ma consumo CPU basso (~0-2%) e RAM contenuta (~350 MB totale)
- **MemAvailable**: 4.2 GB (ancora sopra il livello critico di 500 MB)
- **Swap usato**: ~3.3 GB (in miglioramento)
- **kswapd0**: assente dai top → pressione memoria alleviata
- **Batteria**: 48% (in uso, non in carica)
- **Temperatura**: 32.6°C (normale sotto utilizzo)

Conclusioni: le ottimizzazioni sulle app più pesanti (Motorola IoV, WeWard) rimane efficace. Microsoft AppManager è fastidioso ma non impattante. Il sistema rimane stabile con buon headroom di memoria.

```bash
# Verifica rapida stato attuale
adb_local shell "ps -A | grep -E 'saicmotor|microsoft.appmanager|weward'"
adb_local shell "cmd appops get com.microsoft.appmanager RUN_ANY_IN_BACKGROUND"
adb_local shell "am get-standby-bucket com.microsoft.appmanager"
adb_local shell "cat /proc/meminfo | grep -E 'MemAvailable|SwapFree'"
```




