# Integrazione Alexa

Documentazione per l'invio di messaggi vocali (TTS) ai dispositivi Echo.

---

## 1. Integrazione `alexa_media` (Custom Component)

### Entità Identificate
- **Cucina (1° Echo Dot)**: `media_player.alexa_media_echo_dot_di_carlo` / `notify.alexa_media_echo_dot_di_carlo`
- **Altro Echo Dot**: `media_player.alexa_media_2o_echo_dot_di_carlo` / `notify.alexa_media_2o_echo_dot_di_carlo`

### Metodo di invio consigliato
Il metodo più affidabile è l'utilizzo del servizio generico `notify.send_message`.

#### Esempio YAML (Automazioni/Script)
```yaml
action:
  - service: notify.send_message
    target:
      entity_id: notify.alexa_media_echo_dot_di_carlo
    data:
      message: "Il caffè è pronto!"
```

#### Esempio Pyscript
```python
service.call("notify", "send_message", 
             entity_id="notify.alexa_media_echo_dot_di_carlo", 
             message="Il caffè è pronto!")
```

### Note tecniche
- La piattaforma utilizzata è `alexa_media` (custom component).
- Le entità notify sono create automaticamente per ogni media_player Alexa.
- Per gli annunci (che interrompono brevemente la riproduzione su tutti i dispositivi), utilizzare `notify.alexa_media` con target `media_player.all` o gruppi definiti.

---

## 2. Integrazione `alexa_devices` (Ufficiale HA Core)

Installata da: https://github.com/home-assistant/core/tree/dev/homeassistant/components/alexa_devices

### Entità Identificate (config entry: `01KVAWWZV8PKQ2SV534H2BX801`)
| Dispositivo | Media Player | Notify (TTS) | Sensori aggiuntivi |
|-------------|--------------|--------------|-------------------|
| **Cucina** | `media_player.cucina` | **`notify.cucina_speak`** | `binary_sensor.cucina_connectivity`, `binary_sensor.cucina_motion`, `sensor.cucina_temperature_2`, `sensor.cucina_illuminance`, `sensor.cucina_next_alarm`, `sensor.cucina_next_timer`, `sensor.cucina_next_reminder`, `switch.cucina_do_not_disturb`, `select.cucina_cucina_drop_in`, `switch.cucina_cucina_announcements`, `switch.cucina_cucina_communications` |
| **Camera** | `media_player.camera` | `notify.camera_speak` | `binary_sensor.camera_connectivity`, `binary_sensor.camera_motion`, `sensor.camera_temperature_2`, `sensor.camera_illuminance`, `sensor.camera_next_alarm`, `sensor.camera_next_timer`, `sensor.camera_next_reminder`, `switch.camera_do_not_disturb`, `select.camera_grande_camera_drop_in`, `switch.camera_grande_camera_announcements`, `switch.camera_grande_camera_communications` |
| **Sistema Audio** | `media_player.sistema_audio_2` | `notify.sistema_audio_speak` | `binary_sensor.sistema_audio_connectivity` |
| **Carlo's M67beta** | `media_player.carlo_s_m67beta_2` | `notify.carlo_s_m67beta_speak` | `binary_sensor.carlo_s_m67beta_connectivity`, `sensor.carlo_s_m67beta_next_alarm_2`, `sensor.carlo_s_m67beta_next_timer_2`, `sensor.carlo_s_m67beta_next_reminder_2`, `switch.carlo_s_m67beta_do_not_disturb_2` |
| **Ovunque** | `media_player.ovunque_2` | `notify.ovunque_speak` | `binary_sensor.ovunque_connectivity` |

### Metodo di invio consigliato
Usare **`notify.send_message`** sulle entità `notify.*_speak`.

#### Esempio YAML
```yaml
action:
  - service: notify.send_message
    target:
      entity_id: notify.cucina_speak
    data:
      message: "Il caffè è pronto!"
```

#### Esempio Pyscript
```python
service.call("notify", "send_message", 
             entity_id="notify.cucina_speak", 
             message="Il caffè è pronto!")
```

### Note tecniche
- **NON usare** `media_player.play_media` con `media_content_type: "tts"` → restituisce **Internal Server Error (500)**.
- Il volume TTS è controllato dal **volume "Annunci"** del dispositivo Alexa (app Alexa → Dispositivi → Suoni → Volume annunci), **non** dal `volume_level` del media_player HA.
- Per regolare il volume media: `media_player.volume_set` su `media_player.alexa_echo_dots` (influisce su musica/streaming, non su TTS).
- Le entità `notify.*_announce` usano il tipo "announce" (interrompono la riproduzione).
- Tutto l'integrazione è gestita via config entry UI (non YAML).
- Sensori disponibili: temperatura, illuminanza, allarmi, timer, reminder, connettività, motion, do not disturb, drop-in, annunci, comunicazioni.
- Liste: `todo.carlo_folini_gmail_com_shopping_list`, `todo.carlo_folini_gmail_com_to_do_list`.

### Gruppo `media_player.alexa_echo_dots`
Definito in `groups.yaml` — raggruppa i due Echo Dot (Cucina + Camera) per comandi di riproduzione condivisi (play/stop/volume). Tutti gli script e automazioni usano questo gruppo come target, così entrambi i device rispondono contemporaneamente.

---

## Riepilogo rapido: quale usare?

| Obiettivo | Integrazione | Entità notify |
|-----------|--------------|---------------|
| TTS su Cucina (nuova) | `alexa_devices` | `notify.cucina_speak` |
| TTS su Cucina (legacy) | `alexa_media` | `notify.alexa_media_echo_dot_di_carlo` |
| Annuncio su tutti (legacy) | `alexa_media` | `notify.alexa_media` + target `media_player.all` |
| Controllo volume musica | Entrambe | `media_player.volume_set` su media_player |
|| Controllo volume TTS | `alexa_devices` | Solo da app Alexa (volume annunci) |

---

## Log

Tutti gli script e le automazioni Alexa scrivono messaggi di `info` nei log di Home Assistant tramite l'azione `system_log.write`, per tracciare quale comando viene eseguito:

| Script/Automazione | Messaggio log |
|-------------------|---------------|
| `script.alexa_send_custom` | `Alexa comando testuale: <valore input_text>` |
| `script.alexa_radio_m2o_custom` | `Alexa comando testuale: radio m2o` |
| `script.alexa_radio_m2o_tunein` | `Alexa TuneIn: radio m2o` |
| `script.alexa_timer_9min_custom` | `Alexa comando testuale: attiva un timer da 9 minuti` |
| `script.alexa_stop` | `Alexa Stop: interrompi riproduzione` |
| `automation.alexa_risposta_buongiorno` | `Alexa Buongiorno: avvio sequenza mattutina` |

Per visualizzare i log: **Developer Tools → Log** oppure nei log di HA in Docker.

---

## 3. emulated_hue Bridge per Controllo Dispositivi (Settembre 2026)

### Architettura
| Componente | Indirizzo | Porta | Note |
|------------|-----------|-------|------|
| **Nginx Proxy Manager** | `192.168.0.3` | 80, 81, 443, 8443 | Solo su IP primario |
| **emulated_hue Bridge** | **`192.168.0.48`** | **80** | IP secondario statico su `enp2s0` |

### Configurazione
```yaml
# configuration.yaml
emulated_hue:
  host_ip: 192.168.0.48
  advertise_ip: 192.168.0.48
  listen_port: 80
  expose_by_default: false
  entities:
    input_boolean.buongiorno_alexa:
      name: "Buongiorno"
      hidden: false
    input_boolean.alexa_accendi_uscita:
      name: "Uscita"
      hidden: false
    input_boolean.alexa_accendi_entrata:
      name: "Entrata"
      hidden: false
    input_boolean.alexa_ritorno_a_casa:
      name: "Ritorno a Casa"
      hidden: false
```

### IP Secondario Persistente
```bash
# Aggiunto via NetworkManager (sopravvive al reboot)
sudo nmcli connection modify enp2s0 +ipv4.addresses 192.168.0.48/24
sudo nmcli connection up enp2s0
```
- MAC interfaccia: `90:1B:0E:94:51:1C`
- DHCP: **non riservare** `192.168.0.48` (stesso MAC di `.3`); escluderlo solo dal pool dinamico.

### Entità Espe
| ID Hue | Nome Alexa | Entità HA | Tipo | Automazione Trigger |
|--------|------------|-----------|------|---------------------|
| 45 | Buongiorno | `input_boolean.buongiorno_alexa` | Switch | `automation.alexa_risposta_buongiorno` (auto-reset 5s) |
| — | Uscita | `input_boolean.alexa_accendi_uscita` | Switch | `automation.alexa_modalita_uscita` su `light.uscita` → ON |
| — | Entrata | `input_boolean.alexa_accendi_entrata` | Switch | `automation.alexa_modalita_entrata` su `light.entrata` → ON |
| — | Ritorno a Casa | `input_boolean.alexa_ritorno_a_casa` | Switch | `automation.alexa_ritorno_a_casa` su `light.ritorno_a_casa` → ON |

### Pattern Voice → Automazione
1. **Template Light** (`light.uscita`, `light.entrata`, `light.ritorno_a_casa`, `light.verifica`) backed da rispettivi `input_boolean`
2. **Automation** trigger su `light.<nome>` → `on`
3. **emulated_hue** espone l'`input_boolean` come switch Hue
4. **Alexa** "accendi <nome>" → bridge Hue → `input_boolean` ON → `light.<nome>` ON → automation fires

### Cosa fa ogni comando

| Comando | Azioni principali |
|---------|-------------------|
| **Buongiorno** | Apre tapparella camera grande, dice "Buongiorno Carlo!", avvia radio m2o (auto-reset 5s) |
| **Uscita** | Verifica modalità tethering = Normale, spegne luci, spegne radio, accende luci scale, dice "Arrivederci Carlo!" |
| **Entrata** | Dice "Bentornato Carlo!", accende luce bancone se buio (<50 lux), avvia radio m2o |
| **Ritorno a Casa** | Apre porta garage, dice "Bentornato Carlo!", accende luce bancone se buio (<50 lux), avvia radio m2o |

### TTS
Tutti i TTS usano `notify.send_message` su entità `notify.*_speak` (integrazione `alexa_devices`):
```yaml
- service: notify.send_message
  target:
    entity_id: notify.cucina_speak
  data:
    message: "Comando ricevuto"
```

### Discovery Alexa
Dopo modifiche: **rimuovere** il vecchio device "Verifica" nell'app Alexa (mantenere il bridge), poi:
> "Alexa, scopri dispositivi"

Dovrebbero apparire **Buongiorno** e **Direzione**.

### Log Chiave
```bash
# Bridge descriptor XML
curl http://192.168.0.48/description.xml
# API lights
curl http://192.168.0.48/api/nouser/lights
# SSDP announce (da log HA)
# LOCATION: http://192.168.0.48:80/description.xml
```

### Nota su Porta 80
Alexa **richiede** porta 80 per il bridge Hue emulato. Porta 8300 (precedente) non funziona per discovery. NPM è stato vincolato a `192.168.0.3:80` per liberare `:80` su `.48`.