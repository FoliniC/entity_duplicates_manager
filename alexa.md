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
- Per regolare il volume media: `media_player.volume_set` su `media_player.cucina` (influisce su musica/streaming, non su TTS).
- Le entità `notify.*_announce` usano il tipo "announce" (interrompono la riproduzione).
- Tutto l'integrazione è gestita via config entry UI (non YAML).
- Sensori disponibili: temperatura, illuminanza, allarmi, timer, reminder, connettività, motion, do not disturb, drop-in, annunci, comunicazioni.
- Liste: `todo.carlo_folini_gmail_com_shopping_list`, `todo.carlo_folini_gmail_com_to_do_list`.

---

## Riepilogo rapido: quale usare?

| Obiettivo | Integrazione | Entità notify |
|-----------|--------------|---------------|
| TTS su Cucina (nuova) | `alexa_devices` | `notify.cucina_speak` |
| TTS su Cucina (legacy) | `alexa_media` | `notify.alexa_media_echo_dot_di_carlo` |
| Annuncio su tutti (legacy) | `alexa_media` | `notify.alexa_media` + target `media_player.all` |
| Controllo volume musica | Entrambe | `media_player.volume_set` su media_player |
| Controllo volume TTS | `alexa_devices` | Solo da app Alexa (volume annunci) |