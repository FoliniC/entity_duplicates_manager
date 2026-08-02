# M5 Atom Echo - Bluetooth Proxy Setup

## Data
2026-08-01

## Hardware
- **Device**: M5 Atom Echo (ESP32-PICO-D4)
- **Chip**: ESP32-PICO (single core, 4MB flash, 520KB SRAM)
- **USB**: CP2104 USB-to-UART bridge → `/dev/ttyUSB0`

## Firmware Compilato
- **File**: `/home/carlo/docker/homeassistant/config/m5_atom_echo_bt_proxy_firmware.bin`
- **Tipo**: `firmware.factory.bin` (bootloader + partition table + app)
- **Dimensione**: 1.3 MB (1,322,544 bytes)
- **Build path**: `/home/carlo/docker/homeassistant/config/.esphome/build/m5-atom-echo-bt-proxy/`

## Configurazione ESPHome (m5_atom_echo_bt_proxy.yaml)
```yaml
esphome:
  name: m5-atom-echo-bt-proxy
  friendly_name: "M5 Atom Echo BT Proxy"

esp32:
  board: m5stack-atom
  framework:
    type: arduino

logger:
  level: DEBUG

api:

ota:
  - platform: esphome

wifi:
  ssid: "YOUR_WIFI_SSID"          # ← DA CAMBIARE
  password: "YOUR_WIFI_PASSWORD"  # ← DA CAMBIARE

  ap:
    ssid: "M5-Atom-Echo-BT-Proxy Fallback"
    password: "fallback123"

captive_portal:

bluetooth_proxy:
  active: true
```

## Chiave Crittografia API (API Encryption Key)
```
1QqfQJS2EpjGu/MawdMLv339GxAlxRmCe6JYdXX+4HM=
```
> **IMPORTANTE**: Questa chiave va configurata in Home Assistant quando si aggiunge il dispositivo ESPHome. Senza di essa, HA non può comunicare con il proxy.

## Build Info
- **ESPHome version**: 2026.7.3
- **ESP-IDF**: 5.5.5
- **Target**: esp32 (m5stack-atom)
- **Flash size**: 4MB (0x400000)
- **Partition scheme**: factory (app 0x1c0000, 31% free)
- **RAM usage**: 56.2% (69,988 / 124,580 bytes)
- **Flash usage**: 68.5% (1,256,891 / 1,835,008 bytes)

## Memoria (da build size report)
| Tipo | Usato | Totale | % |
|------|-------|--------|---|
| IRAM | 106,735 B | 131,072 B | 81.4% |
| DRAM | 69,988 B | 124,580 B | 56.2% |
| Flash Code | 943,180 B | - | - |
| Flash Data | 184,412 B | - | - |
| RTC SLOW | 56 B | 8,192 B | 0.7% |

## Flash del Firmware

### Metodo 1: ESPHome Web Flasher (consigliato)
1. Apri browser sul **tuo PC**: https://web.esphome.io/
2. Collega M5 Atom Echo via USB al **tuo PC**
3. Clicca **"Connect"** → seleziona porta (es. `ttyUSB0` / `COM3`)
4. Clicca **"Install"** → **"Install from file"**
5. Seleziona: `m5_atom_echo_bt_proxy_firmware.bin`
6. Attendi completamento (30-60 sec)

### Metodo 2: esptool (linea comando)
```bash
# Linux/macOS
esptool --port /dev/ttyUSB0 --baud 460800 write-flash -z 0x0 m5_atom_echo_bt_proxy_firmware.bin

# Windows
esptool --port COM3 --baud 460800 write-flash -z 0x0 m5_atom_echo_bt_proxy_firmware.bin
```

## Prima Configurazione WiFi
Dopo il flash, il dispositivo:
1. Crea hotspot: **"M5-Atom-Echo-BT-Proxy Fallback"** (password: `fallback123`)
2. Collega telefono/PC a quell'hotspot
3. Apri browser: `http://192.168.4.1`
4. Inserisci credenziali **tua WiFi di casa** (SSID + password)
5. Clicca "Save" → il dispositivo si riavvia e si connette alla tua rete

## Integrazione Home Assistant

### 1. Scoperta automatica
- HA rileva il dispositivo via mDNS/ESPHome
- **Impostazioni → Dispositivi e servizi → ESPHome** → "1 dispositivo trovato" → **Configura**
- Inserisci **API Encryption Key**: `1QqfQJS2EpjGu/MawdMLv339GxAlxRmCe6JYdXX+4HM=`

### 2. Bluetooth Proxy in HA
- **Impostazioni → Dispositivi e servizi → Bluetooth**
- Vedrai: **"M5 Atom Echo BT Proxy"** come adapter **Attivo**
- Stato: **Connesso** (verde)

### 3. Utilizzo
Il proxy ora:
- Scansiona BLE in background
- Inoltra advertisement a HA via API
- Sensori Xiaomi Mijia (stock + custom), SwitchBot, Govee, ecc. appaiono automaticamente in **Bluetooth → Dispositivi rilevati**

## Note su Xiaomi Mijia
| Firmware sensore | Funziona via Proxy? |
|-----------------|---------------------|
| **Stock (LYWSD03MMC, CGG1, MJ_HT_V1)** | ✅ SÌ - il proxy ESP32 gestisce encryption |
| **Custom (ATC_MiThermometer, OpenMiThermometer, pvvx)** | ✅ SÌ - broadcast in chiaro |
| **Altri BLE (SwitchBot, Govee, Inkbird, Qingping)** | ✅ SÌ |

## Troubleshooting

| Problema | Soluzione |
|----------|-----------|
| Non appare in HA | Verifica mDNS (router), firewall, stessa VLAN |
| "Encryption key mismatch" | Reinserisci chiave esatta: `1QqfQJS2EpjGu/MawdMLv339GxAlxRmCe6JYdXX+4HM=` |
| Si disconnette spesso | Alimentazione USB insufficiente → usa hub alimentato o power bank |
| Non vede sensori | Riavvia proxy (scollega/ricollega USB), verifica RSSI > -80dBm |

## Log Utili
```bash
# Log ESPHome (da HA: Dispositivo → Logs)
# O via seriale (115200 baud):
screen /dev/ttyUSB0 115200
```

## File Correlati
- Config: `/home/carlo/docker/homeassistant/config/m5_atom_echo_bt_proxy.yaml`
- Firmware: `/home/carlo/docker/homeassistant/config/m5_atom_echo_bt_proxy_firmware.bin`
- Build dir: `/home/carlo/docker/homeassistant/config/.esphome/build/m5-atom-echo-bt-proxy/`

---
*Generato automaticamente durante setup del 2026-08-01*