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
- **Ruolo**: IP Camera RTSP dedicata per monitoraggio continuo.
- **Sistema Operativo**: Android 10 (Magic UI / Kirin 970).
- **App Principale**: `com.pas.webcam` (**IP Webcam**).
- **App Backup**: `com.dev47apps.droidcam` (**DroidCam**).
- **Porte di Streaming**:
  - **HTTP / MJPEG**: Port `8080` (es. `http://<IP_PHONE>:8080/video`)
  - **RTSP**: Port `8554` (es. `rtsp://<IP_PHONE>:8554/video`)
- **Stato Ottimizzazione ADB**:
  - 63 pacchetti bloatware disabilitati (Huawei AppGallery, Huawei Search, Google Apps pesanti).
  - Pressione Swap azzerata (kswapd0 < 1%).
  - Temperatura stabilizzata a ~31°C sotto alimentazione USB continua.
- **Documentazione Dettagliata**:
  - [`OTTIMIZZAZIONE_HONOR_COL-L29_POST_IP_CAMERA.md`](./OTTIMIZZAZIONE_HONOR_COL-L29_POST_IP_CAMERA.md)
  - [`DIAGNOSTICA_HONOR_COL-L29_PRE_OTTIMIZZAZIONE.md`](./DIAGNOSTICA_HONOR_COL-L29_PRE_OTTIMIZZAZIONE.md)

### 2. Redmi Note 9S
- **Ruolo**: Dispositivo di diagnostica / IP Camera di supporto.
- **Documentazione Dettagliata**:
  - [`DIAGNOSTICA_REDMI_NOTE_9S_PRE_OTTIMIZZAZIONE.md`](./DIAGNOSTICA_REDMI_NOTE_9S_PRE_OTTIMIZZAZIONE.md)

---

## 📲 App StreamPack (push RTMP → MediaMTX)

Le telecamere smartphone usano l'app custom **StreamPack** (`io.github.thibaultbee.streampack.app`, fork/build da ThibaultBee) che effettua lo streaming H264/AAC via **RTMP** verso il server MediaMTX (`192.168.0.3:1935`), consentendo l'ingest automatico e senza watermark.

### Architettura e Inoltro di Rete
```
StreamPack (Redmi Note 11 Pro 5G via USB Tethering)
  ↓ [RTMP su interfaccia rndis0]
Gateway OpenWrt RNDIS (10.203.33.202:1935)
  ↓ [DNAT 1935 + SNAT Masquerade su br-lan]
Debian Server MediaMTX (192.168.0.3:1935 / path 'live/telefono')
  ↓ [RTSP :8890/live/telefono]
Frigate NVR & Home Assistant
```

### Percorsi dei File nel Progetto
- **Repository Locale**: `/home/carlo/streampack-telefono/`
- **Repository GitHub**: `FoliniC/streampack-telefono` (branch `main`)
- **File di Configurazione predefinita (Sorgenti Kotlin)**:
  - Repository storage: `/home/carlo/streampack-telefono/app/src/main/java/io/github/thibaultbee/streampack/app/data/storage/StorageRepository.kt`
  - Manager configurazione: `/home/carlo/streampack-telefono/app/src/main/java/io/github/thibaultbee/streampack/app/data/config/StreamConfig.kt`
- **File di Configurazione dinamica sullo Smartphone**:
  - Percorso file JSON: `/sdcard/Download/streampack.json`
- **Script Auto-Healing Tunnel ADB/scrcpy**:
  - Script locale: `/home/carlo/Desktop/scrcpy-redmi.sh`

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
Tramite il tunnel ADB stabilito con il router (porta `5555` / script `/home/carlo/Desktop/scrcpy-redmi.sh`):
```bash
# Installazione diretta APK
adb -s 127.0.0.1:5555 install -r -g /home/carlo/Downloads/streampack-telefono-debug.apk

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

