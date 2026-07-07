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




