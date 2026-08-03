# Xiaomi BLE Setup & Troubleshooting - Documentazione Completa

**Data:** 2026-08-02  
**Account Xiaomi:** 1655176526  
**Server Xiaomi:** `de` (Europa/Frankfurt - `account.xiaomi.com/fe`)

---

## 📋 Sommario Esecutivo

Problema iniziale: Impossibile aggiornare M5Stack Atom Echo (MAC `90:15:06:FA:E7:F8`) via OTA. Risolto con flash USB del firmware **BT Proxy** con credenziali WiFi corrette.

---

## 🔧 Dispositivo: M5Stack Atom Echo BT Proxy

### Identificazione
- **MAC:** `90:15:06:FA:E7:F8`
- **Chip:** ESP32-PICO-D4 (rev 1.1)
- **Firmware:** ESPHome 2025.5.2 (compilato 2026-08-02 19:37:35)
- **IP Statico:** `192.168.0.171`
- **Gateway:** `192.168.0.11` (router OpenWrt TP-Link AC1750 C7)
- **DNS:** `8.8.8.8`, `8.8.4.4`

### Configurazione WiFi
```yaml
wifi:
  ssid: "CPE_2.4G_112E90"           # Rete 2.4GHz (Channel 6, HT20)
  password: "Qv&#$SG8MGb1i"         # Da secrets.yaml
  manual_ip:
    static_ip: 192.168.0.171
    gateway: 192.168.0.11
    subnet: 255.255.255.0
    dns1: 8.8.8.8
    dns2: 8.8.4.4
```

### File Sorgente: `/home/carlo/docker/homeassistant/config/m5_atom_echo_bt_proxy.yaml`
```yaml
esphome:
  name: m5-atom-echo-bt-proxy
  friendly_name: "M5 Atom Echo BT Proxy"
  min_version: 2025.5.2

esp32:
  board: m5stack-atom
  framework:
    type: arduino

api:
  encryption:
    key: "1QqfQJS2EpjGu/MawdMLv339GxAlxRmCe6JYdXX+4HM="

ota:
  - platform: esphome

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  manual_ip:
    static_ip: 192.168.0.171
    gateway: 192.168.0.11
    subnet: 255.255.255.0
    dns1: 8.8.8.8
    dns2: 8.8.4.4

bluetooth_proxy:
  active: true
```

### Firmware Compilato
- **Factory:** `/home/carlo/docker/homeassistant/config/.esphome/build/m5-atom-echo-bt-proxy/.pioenvs/m5-atom-echo-bt-proxy/firmware.factory.bin` (1.66 MB)
- **OTA:** `/home/carlo/docker/homeassistant/config/.esphome/build/m5-atom-echo-bt-proxy/.pioenvs/m5-atom-echo-bt-proxy/firmware.ota.bin` (1.26 MB)

---

## 🔌 Flash USB (Modalità Bootloader)

### Hardware
- **Convertitore USB-UART:** FTDI FT232 (`0403:6001`)
- **Porta:** `/dev/ttyUSB0`
- **Cavo:** Deve essere **cavo dati** (non solo ricarica)

### Procedura Modalità Bootloader (M5Stack Atom Echo)
1. Scollega USB
2. **Tieni premuto pulsante BOOT** (quello piccolo, non reset)
3. Ricollega USB tenendo premuto BOOT
4. Attendi 2-3 secondi → rilascia BOOT
5. LED spento/fisso = in modalità download

### Comando Flash (baud 115200 per stabilità)
```bash
docker run --rm --device /dev/ttyUSB0 \
  -v /home/carlo/docker/homeassistant/config:/config \
  python:3.11-slim bash -c "
    pip install esptool -q &&
    esptool.py --port /dev/ttyUSB0 --baud 115200 \
      --chip esp32 --before default-reset --after hard-reset \
      write-flash -z --flash-mode dio --flash-freq 80m --flash-size 4MB \
      0x0 /config/.esphome/build/m5-atom-echo-bt-proxy/.pioenvs/m5-atom-echo-bt-proxy/firmware.factory.bin
  "
```

---

## 🌐 Rete Locale - Router OpenWrt (192.168.0.11)

### Hardware
- **Router:** TP-Link Archer C7 v5 (AC1750)
- **Firmware:** OpenWrt 24.10 (LuCI)
- **SSH:** `ssh -i /config/.ssh/router_key root@192.168.0.11`

### WiFi 2.4GHz (`radio1`)
```bash
# Config attuale
wireless.radio1=wifi-device
wireless.radio1.type='mac80211'
wireless.radio1.path='platform/ahb/18100000.wmac'
wireless.radio1.band='2g'
wireless.radio1.channel='6'
wireless.radio1.htmode='HT20'

wireless.default_radio1=wifi-iface
wireless.default_radio1.device='radio1'
wireless.default_radio1.network='lan'
wireless.default_radio1.mode='ap'
wireless.default_radio1.ssid='CPE_2.4G_112E90'
wireless.default_radio1.encryption='psk2'
wireless.default_radio1.key='Qv&#$SG8MGb1i'
```

### Query Config Wireless
```bash
ssh -i /config/.ssh/router_key root@192.168.0.11 \
  "uci show wireless | grep -E '(radio|ssid|channel|band|ht_capab)'"
```

---

## 📱 Dispositivi Xiaomi BLE Rilevati (Server `de`, Home `332001039904`)

| Dispositivo | Tipo | MAC | BLE Key / Token | Model | ID |
|-------------|------|-----|-----------------|-------|-----|
| **Mi Temperature and Humidity Monitor 2** | Sensore BLE | `A4:C1:38:26:31:16` | **BLE KEY:** `926c7b92ffd7b7e4ff10cceaa1c39884` | `miaomiaoce.sensor_ht.t2` | `blt.4.1pqko3j89go00` |
| **Xiaomi Smart Band 8 Pro** | Wearable | `54:2F:04:E4:ED:F3` | **TOKEN:** `fe8bffd6b0fae30d2c5ebba029429c7b` | `lchz.watch.m67gl` | `738202714` |
| **Xiaomi Smart Band 10** | Wearable | `04:34:C3:2F:5D:DE` | **TOKEN:** `7db376de0860a4a6994d0b201fb1c4e9` | `miwear.watch.o66gl` | `955911651` |

> **Nota:** Solo il sensore temperatura/umidità (Miaomiaoce) ha **BLE KEY** (dispositivo BLE puro). Le Smart Band usano **TOKEN** (dispositivi associati via app Mi Fitness).

---

## 🔐 Bindkey per Home Assistant (Xiaomi BLE Integration)

### Formato configuration.yaml
```yaml
xiaomi_ble:
  bindkeys:
    # Mi Temperature and Humidity Monitor 2
    "a4c138263116": "926c7b92ffd7b7e4ff10cceaa1c39884"
    # Xiaomi Smart Band 8 Pro
    "542f04e4edf3": "fe8bffd6b0fae30d2c5ebba029429c7b"
    # Xiaomi Smart Band 10
    "0434c32f5dde": "7db376de0860a4a6994d0b201fb1c4e9"
```

### Formato UI (Impostazioni → Dispositivi e Servizi → Xiaomi BLE → Configura → Bindkeys)
```
a4c138263116: 926c7b92ffd7b7e4ff10cceaa1c39884
542f04e4edf3: fe8bffd6b0fae30d2c5ebba029429c7b
0434c32f5dde: 7db376de0860a4a6994d0b201fb1c4e9
```

> **MAC format:** minuscolo, senza due punti (`:`)

---

## 🛠️ Estrazione Bindkey/Token - Tool Utilizzati

### 1. Xiaomi Cloud Tokens Extractor (Piotr Machowski)
**Repo:** https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor

#### Installazione Locale (venv)
```bash
cd ~
python3 -m venv xiaomi-token-venv
source xiaomi-token-venv/bin/activate
git clone https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor.git
cd Xiaomi-cloud-tokens-extractor
pip install -r requirements.txt
# requirements: requests, pycryptodome, charset-normalizer, Pillow, colorama
```

#### Esecuzione Interattiva (richiede CAPTCHA)
```bash
python3 token_extractor.py -u "1655176526" -s "de" -l "INFO"
# Seleziona 'p' per password
# Inserisci password
# Risolvi CAPTCHA nel browser che si apre
```

#### Output Atteso
```
Devices found for server "de" @ home "332001039904":
   ---------
   NAME:     Mi Temperature and Humidity Monitor 2
   ID:       blt.4.1pqko3j89go00
   BLE KEY:  926c7b92ffd7b7e4ff10cceaa1c39884
   MAC:      A4:C1:38:26:31:16
   TOKEN:    3bed0035d30c065707c430f5
   MODEL:    miaomiaoce.sensor_ht.t2
   ---------
   ...
```

### 2. Tool Web (Alternativa Senza Installazione)
**URL:** https://xiaomi-cloud-tokens-extractor.vercel.app/
- Stesso autore (Piotr Machowski)
- Gestisce CAPTCHA nel browser
- Stesso output del CLI

---

## 🔧 Troubleshooting Comuni

### OTA Fail - "Connection reset by peer"
**Causa:** Firmware troppo grande per partizione OTA o partizione corrotta.
**Soluzione:** Flash USB completo (`firmware.factory.bin` include bootloader + partition table).

### Porta 8125 Occupata
**Causa:** Istanza HA di test in `host network mode` su porta 8125.
**Soluzione:**
```bash
docker stop homeassistant-test mariadb-test mosquitto-test
docker update --restart=no homeassistant-test mariadb-test mosquitto-test
```

### BT Proxy Non Si Connette WiFi
**Cause possibili:**
1. Credenziali errate in `secrets.yaml`
2. SSID 5GHz (ESP32 supporta solo 2.4GHz)
3. Password con caratteri speciali non escapati
4. MAC filtering / AP isolation sul router

**Verifica:** `ping 192.168.0.171` → se risponde, connesso.

### Xiaomi BLE "Invalid Password"
**Cause:**
1. **2FA attivo** → serve **Password per app** (non password principale)
   - Crea su: https://account.xiaomi.com/fe → Sicurezza → Password per app
2. **Server sbagliato** → Prova `de` (Europa), `cn` (Cina), `us`, `ru`, `sg`, `in`, `i2`, `tw`
3. **Dispositivo non bindato** → Deve essere aggiunto in **Mi Home / Xiaomi Home** app

---

## 📂 File di Configurazione Principali

| File | Percorso | Descrizione |
|------|----------|-------------|
| BT Proxy YAML | `/config/m5_atom_echo_bt_proxy.yaml` | Config ESPHome BT Proxy |
| Secrets | `/config/secrets.yaml` | WiFi credentials, API keys |
| ESPHome Build | `/config/.esphome/build/m5-atom-echo-bt-proxy/` | Firmware compilato |
| HA Config | `/config/configuration.yaml` | Config HA (http: server_port: 8124) |
| Router SSH Key | `/config/.ssh/router_key` | Chiave SSH router OpenWrt |
| Xiaomi Token Venv | `~/xiaomi-token-venv/` | Virtual env token extractor |
| Xiaomi Repo | `~/Xiaomi-cloud-tokens-extractor/` | Script estrazione token |

---

## 🔗 Comandi Utili Rapidi

### Verifica Stato BT Proxy
```bash
ping -c 3 192.168.0.171
curl -s http://192.168.0.171/ | head -5
```

### Test API ESPHome (con encryption key)
```python
import asyncio
from aioesphomeapi import APIClient

async def test():
    key = "1QqfQJS2EpjGu/MawdMLv339GxAlxRmCe6JYdXX+4HM="
    client = APIClient("192.168.0.171", 6053, password="", noise_psk=key)
    await client.connect(login=True)
    info = await client.device_info()
    print(f"Device: {info.name} - {info.esphome_version}")
    await client.disconnect()

asyncio.run(test())
```

### Verifica Xiaomi BLE in HA
```bash
# Entities Xiaomi BLE
curl -s -H "Authorization: Bearer $HA_TOKEN" \
  http://localhost:8123/api/states | jq '.[] | select(.entity_id | contains("xiaomi"))'
```

### Log BT Proxy (se accessibile)
```bash
# Via ESPHome dashboard o
esphome logs m5_atom_echo_bt_proxy.yaml
```

---

## 📝 Note Finali

1. **BT Proxy funziona** su `192.168.0.171` come Bluetooth Proxy passivo per HA
2. **Bindkey estratte** per 3 dispositivi - pronte per configurazione Xiaomi BLE in HA
3. **Instance HA test** disabilitate (porta 8125 liberata)
4. **Produzione HA** su porta 8123 (nginx proxy su 8124 come configurato)
5. **Prossimo step:** Aggiungere bindkey in HA → Xiaomi BLE → Configura → Bindkeys

---

*Documento generato automaticamente dalla sessione di troubleshooting del 2026-08-02*