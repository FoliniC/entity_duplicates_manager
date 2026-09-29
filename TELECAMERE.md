# Sistema di Videosorveglianza, NVR e Telecamere IP

Documentazione centralizzata dell'architettura di videosorveglianza dell'ambiente domotico: NVR, rilevamento AI (Frigate), container Agent DVR e dispositivi IP Camera (inclusi smartphone riciclati come webcam RTSP).

---

## 📌 Architettura Generale

L'infrastruttura di videosorveglianza si articola su tre componenti chiave:

1. **Agent DVR (NVR Centralizzato)**: Container Docker residente sul server Debian (`192.168.0.3`) per la registrazione video continuous/event-based e la gestione dei flussi RTSP.
2. **Frigate (Rilevamento Oggetti & AI)**: Gestione degli eventi di motion/person detection via MQTT ed elaborazione degli allarmi.
3. **Dispositivi IP Camera**:
   - Telecamere IP dedicate (Cucina/Balcone, Locale Tecnico/Ingresso).
   - Smartphone riciclati (es. HONOR COL-L29) trasformati in stream RTSP/MJPEG con app **IP Webcam**.

---

## 📹 Agent DVR (Container NVR)

- **Container Name**: `agentdvr`
- **Immagine Docker**: `doitandbedone/ispyagentdvr:latest`
- **Network Mode**: `host` (condivide lo stack di rete del server Debian `192.168.0.3`)
- **Storage Media**: `/mnt/ha_storage/agentdvr/media` (registrazioni salvate su disco rigido secondario)
- **Configurazione Docker Compose**:
  ```yaml
  agentdvr:
    image: doitandbedone/ispyagentdvr:latest
    container_name: agentdvr
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./homeassistant/config/custom-cont-init.d:/custom-cont-init.d
      - ./agentdvr/config:/config
      - /mnt/ha_storage/agentdvr/media:/media
      - ./agentdvr/commands:/commands
    environment:
      - TZ=Europe/Rome
      - PUID=1000
      - PGID=1000
  ```

---

## 🧠 Frigate & Automazioni Home Assistant

Frigate pubblica gli eventi di rilevamento sul topic MQTT `frigate/events`. Home Assistant processa tali messaggi e invia notifiche push istantanee sullo smartphone principale (`Redmi Note 13 Pro 5G`).

### Automazioni Attive in Home Assistant:

| Automazione | Topic MQTT / Condizione | Notifica | File YAML |
|---|---|---|---|
| **Frigate: Persona rilevata cucina** | `camera == "cucina"` e `zone == "balcone"` | Notifica push con tag `frigate_cucina_person` | `automations/frigate_cucina_person.yaml` |
| **Frigate: Persona rilevata locale tecnico** | `camera == "locale_tecnico"` e `zone == "ingresso_locale_tecnico_ok"` | Notifica push con tag `frigate_locale_tecnico_person` | `automations/frigate_locale_tecnico_person.yaml` |

---

## 📱 Smartphone convertiti in IP Camera (RTSP / MJPEG)

### 1. HONOR COL-L29 (Honor 10)
|- **Ruolo**: IP Camera RTSP dedicata per monitoraggio continuo.
|- **Sistema Operativo**: Android 10 (Magic UI / Kirin 970).
|- **Collegamento Rete**: WiFi su rete locale (`192.168.0.x`)
|- **App Principale**: `com.pas.webcam` (**IP Webcam**).
|- **App Backup**: `com.dev47apps.droidcam` (**DroidCam**).
|- **Porte di Streaming**:
|  - **HTTP / MJPEG**: Port `8080` (es. `http://<IP_PHONE>:8080/video`)
|  - **RTSP**: Port `8554` (es. `rtsp://<IP_PHONE>:8554/video`)

### 2. LG-X150 (Android 5.0.2 / SDK 21)
|- **Ruolo**: Dispositivo di diagnostica ADB (root richiesto).
|- **Sistema Operativo**: Android 5.0.2 (SDK 21).
|- **Collegamento Rete**: WiFi su rete locale (`192.168.0.x`). NON è collegato al router via USB — è usato per test/debug ADB diretto via cavo USB verso Debian.
|- **App Principale**: Nessuna — configurazione di rete e ADB via `settings put`.
|- **Note**: Il telefono non è mai stato rootato; le impostazioni di ottimizzazione e ADB vengono applicate via `settings put`. Il tethering USB è **disabilitato**; la rete avviene esclusivamente via WiFi.
- **Stato Ottimizzazione ADB**:
  - 63 pacchetti bloatware disabilitati (Huawei AppGallery, Huawei Search, Google Apps pesanti).
  - Pressione Swap azzerata (kswapd0 < 1%).
  - Temperatura stabilizzata a ~31°C sotto alimentazione USB continua.
- **Documentazione Dettagliata**:
  - [`OTTIMIZZAZIONE_HONOR_COL-L29_POST_IP_CAMERA.md`](./OTTIMIZZAZIONE_HONOR_COL-L29_POST_IP_CAMERA.md)
  - [`DIAGNOSTICA_HONOR_COL-L29_PRE_OTTIMIZZAZIONE.md`](./DIAGNOSTICA_HONOR_COL-L29_PRE_OTTIMIZZAZIONE.md)

### 2. Redmi Note 9S
|- **Ruolo**: Dispositivo di diagnostica / IP Camera di supporto.
|- **Documentazione Dettagliata**:
|  - [`DIAGNOSTICA_REDMI_NOTE_9S_PRE_OTTIMIZZAZIONE.md`](./DIAGNOSTICA_REDMI_NOTE_9S_PRE_OTTIMIZZAZIONE.md)

### 3. Redmi Note 11 Pro 5G (c9977cf0)
|- **Collegamento Rete**: USB tethering con **router OpenWrt** (non collegato a Debian). IP su LAN `192.168.0.x` tramite DHCP.
|- **Accesso ADB**:
|  - Tunnel ADB tramite router → Debian: `adb connect 127.0.0.1:5555` (port forwarding da `scrpy-redmi.sh` su router)
|  - Wireless (se abilitato): `adb connect 192.168.0.x:5555`
|- **Ruolo**: Accesso internet alternativo (USB tethering Debian ↔ Windows 11) — **NON** camera principale
|- **Sistema Operativo**: Android 14 (SDK 36)
|- **Collegamento Rete**: USB tethering **alternativo** (collegato a Debian o Windows 11) per accesso internet
|- **App Webcamera (opzionale)**: `io.github.thibaultbee.streampack.app` (**StreamPack**) — utilizzabile **in alternativa** al Note 11 Pro 5G
|- **Porta streaming opzionale**: `rtsp://<IP_PHONE>:8080/video` (se StreamPack RTSP push configurata)
|  ```bash
|  adb -s <serial> shell am start -n io.github.thibaultbee.streampack.app/.MainActivity -e url http://192.168.0.3:1935/live/telefono
|  ```

---

## 📲 App StreamPack (push RTMP → MediaMTX)

Le telecamere smartphone usano l'app custom **StreamPack** (`io.github.thibaultbee.streampack.app`, fork/build da ThibaultBee) che effettua lo streaming H264/AAC via **RTMP** verso il server MediaMTX (`192.168.0.3:1935`), consentendo l'ingest automatico e senza watermark.

### Architettura e Inoltro di Rete
```
Redmi Note 11 Pro 5G (rndis0, IP dinamico) → Router OpenWrt usb0 (IP dinamico)
  → alias dinamico <subnet>.10 su Debian (192.168.0.3 / MediaMTX:1935)
  → RTMP path live/telefono → MediaMTX RTSP :8890 → Frigate locale_tecnico
```

#### StreamPack su USB tethering anche in modalità Intranet — verificato 2026-09-16

Il tethering RNDIS può restare **attivo come link locale** anche quando il router è in **Intranet**: la default route del router resta `default via 192.168.0.3 dev br-lan metric 9`; non va sostituita con usb0. Il flusso RTMP usa invece la subnet USB direttamente.

1. Ottenere il lease USB su `usb0` **senza aggiungere una default route**; quindi ricavare `ALIAS="${USB0_IP%.*}.10"`.
2. Sul router: `proxy_arp=1`, neighbor proxy per `ALIAS`, route `ALIAS via 192.168.0.3 dev br-lan`, e masquerade da `<subnet>.0/24` verso `192.168.0.3:1935`.
3. Su Debian: assegnare `ALIAS/32` a `enp2s0`; MediaMTX ascolta su `:1935`.
4. Scrivere nell'app: `rtmp://ALIAS:1935/live/telefono` (mai un IP storico fisso).

Esempio verificato: telefono `rndis0=10.101.166.82`, router `usb0=10.101.166.9`, alias Debian `10.101.166.10`; il router è rimasto in Intranet. Evidenze end-to-end: MediaMTX `is publishing to path 'live/telefono'` / `stream is available and online`, e Frigate `locale_tecnico.camera_fps≈5`.

Gli script `/usr/bin/streampack-rndis-configure.sh` (router) e `host_scripts/streampack_alias_sync_tick.sh` (Debian) mantengono questa sincronizzazione dinamica.

| **Telefono origine dello stream** | Collegamento | IP assegnato | Porta streaming | Destinazione | Note |
|---|---|---|---|---|---|
| Redmi Note 11 Pro 5G (`c9977cf0`) | USB tethering via router OpenWrt | DHCP LAN `192.168.0.x` | RTMP `10.203.33.202:1935/live/telefono` | MediaMTX Debian `192.168.0.3:1935` | **App principale StreamPack** |
| Redmi Note 13 Pro 5G (alternativo) | USB tethering → Debian/Windows | DHCP LAN `192.168.0.x` | RTSP/MJPEG `192.168.0.x:8554` | HA Frigate | Usato come webcam di backup |

### Percorsi dei File nel Progetto
- **Repository Locale**: `/home/carlo/streampack-telefono/`
- **Repository GitHub**: `FoliniC/streampack-telefono` (branch `main`)
- **File di Configurazione predefinita (Sorgenti Kotlin)**:
  - Repository storage: `/home/carlo/streampack-telefono/app/src/main/java/io/github/thibaultbee/streampack/app/data/storage/StorageRepository.kt`
  - Manager configurazione: `/home/carlo/streampack-telefono/app/src/main/java/io/github/thibaultbee/streampack/app/data/config/StreamConfig.kt`
- **File di Configurazione dinamica sullo Smartphone**:
|  - **Percorso file JSON dinamico**: `/sdcard/Download/streampack.json` (salvato dall'app tramite "Salva")
|  - **Percorso alternativo (Internal Storage)**: `/data/data/io.github.thibaultbee.streampack.app/files/streampack.json` (default; non accessibile senza root)
|- **Script Auto-Healing Tunnel ADB/scrcpy**:
|  - Script `scrpy-redmi.sh` gira sul **router OpenWrt** (tunnel ADB → Debian)
|  - Accesso ADB: `adb connect 192.168.0.x:5555` oppure tunnel SSH da Debian → router
|  - Controllo UI: `scrcpy --tcpip=192.168.0.x:5555`

---

### 🛠️ Procedura di Modifica, Compilazione, Download, Deploy e Test

#### 1. Modifica del Sorgente
Per modificare la configurazione o l'URL predefinito nel codice:
```bash
cd /home/carlo/streampack-telefono
# Modifica i file in app/src/main/java/...
git add .
git commit -m "Update RTMP endpoint configuration"
git push origin main
```

#### 2. Compilazione Automatica (CI/CD GitHub Actions)
La spinta sul branch `main` attiva automaticamente il workflow `.github/workflows/build.yml`.
Per monitorare lo stato di compilazione:
```bash
gh run watch $(gh run list --repo FoliniC/streampack-telefono --limit 1 --json databaseId -q '.[0].databaseId') --repo FoliniC/streampack-telefono
```

#### 3. Download dell'APK compilato
A compilazione ultimata (`✓ Build debug APK`), scaricare l'artefatto APK:
```bash
# Scarica l'artefatto GitHub Actions ed estrae app-debug.apk
gh run download --repo FoliniC/streampack-telefono -n streampack-debug-apk -D /tmp/streampack-latest
cp /tmp/streampack-latest/app-debug.apk /home/carlo/Downloads/streampack-telefono-debug.apk
```

#### 4. Deploy e Installazione sul Telefono via ADB
|Tramite il tunnel ADB stabilito con il router (porta 5555) o ADB wireless (sezione `### 3. Redmi Note 11 Pro 5G`):
|```bash
|# Tunnel ADB tramite router → Debian (se non in wireless)
|ssh -L 5555:localhost:5555 carlo@192.168.0.11
|adb connect 127.0.0.1:5555  # oppure: adb connect 192.168.0.x:5555 (wireless)
|
|# Installazione diretta APK (app StreamPack principale → Note 11)
|adb -s 127.0.0.1:5555 install -r -g /home/carlo/Downloads/streampack-telefono-debug.apk
|```

# Aggiornamento file di configurazione JSON sul telefono (opzionale)
adb -s 127.0.0.1:5555 shell 'cat << "EOF" > /sdcard/Download/streampack.json
{
  "url": "rtmp://10.203.33.202:1935/live/telefono",
  "autostart": true,
  "autostart_delay_ms": 1000,
  "auto_reconnect": true,
  "reconnect_interval_sec": 5
}
EOF'
```

#### 5. Esecuzione e Test
Avvio dell'applicazione tramite ADB intent:
```bash
# Riavvia l'app e avvia MainActivity
adb -s 127.0.0.1:5555 shell am force-stop io.github.thibaultbee.streampack.app
adb -s 127.0.0.1:5555 shell am start -n io.github.thibaultbee.streampack.app/.MainActivity

# Verifica ricezione stream RTMP in MediaMTX su Debian
docker logs mediamtx --tail 20

# Verifica logcat dell'app sul telefono
adb -s 127.0.0.1:5555 logcat -d | grep -iE "MainActivity|StreamConfig|RtmpEndpoint"
```

---

### ⚠️ Requisiti di Rete e Regole Router (OpenWrt)

1. **IP Gateway USB Tethering**:
   - L'interfaccia `rndis0` / `usb0` assegna all'OpenWrt router l'IP `10.203.33.202`. L'URL di destinazione RTMP dall'app deve puntare a `rtmp://10.203.33.202:1935/live/telefono`.
2. **Inoltro DNAT & SNAT Masquerade su OpenWrt**:
   - **DNAT**: Inoltra il traffico in ingresso sulla porta `1935` della `wan` verso `192.168.0.3:1935`.
   - **SNAT Masquerade** (FONDAMENTALE): Poiché il gateway di default del server Debian è `192.168.0.1` (e non il router OpenWrt `192.168.0.11`), i pacchetti in arrivo dalla subnet USB (`10.203.33.0/24`) richiedono il masquerade su `br-lan`:
     ```bash
     nft add rule inet fw4 srcnat oifname "br-lan" ip daddr 192.168.0.3 tcp dport 1935 masquerade
     ```

---

### 🚨 Problemi Aperti & Attività In Corso

1. **Stabilità Handshake RTMP / Eccezione `createStream()`**:
   - **Sintomo**: L'app stabilisce la connessione TCP RTMP verso `10.203.33.202:1935` (MediaMTX registra `[RTMP] conn opened`), ma `RtmpEndpoint` segnala occasionalmente `IllegalArgumentException: You must call createStream() before publish()`, provocando l'interruzione della sessione RTMP.
   - **Causa in corso di analisi**: Verificare l'ordine di chiamata tra `connect()`, `createStream()` e `publish()` nella classe di negoziazione RTMP della libreria StreamPack quando si utilizza un endpoint RTMP con app/stream key disaccoppiate (`/live/telefono`).

2. **Gestione del Processo in Background su MIUI (Android 13)**:
   - **Sintomo**: Dopo un riavvio via ADB, il sistema MIUI talvolta forza la chiusura del processo (`ActivityManager: Process died: prcp CRE`).
   - **Azione richiesta**: Configurare i permessi di risparmio energetico su MIUI per evitare l'uccisione dell'activity quando lo schermo si spegne o l'app è in background.

---

## 🔗 Riferimenti & Documentazione Correlata
- **Rete Locale & Routing**: [`RETE_LOCALE.md`](./RETE_LOCALE.md)
- **Ottimizzazione Telefono Router (Redmi Note 11 Pro 5G)**: [`OTTIMIZZAZIONE_TELEFONO.md`](./OTTIMIZZAZIONE_TELEFONO.md)

