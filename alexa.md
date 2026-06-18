# Integrazione Alexa (alexa_devices)

Dettagli per l'invio di messaggi vocali (TTS) ai dispositivi Echo tramite l'integrazione `alexa_devices`.

## Entità Identificate
- **Cucina**: `notify.cucina_speak` (Echo Dot 5th Gen)
- **Camera**: `notify.camera_speak`
- **Ovunque**: `notify.ovunque_announce` (per annunci di gruppo)

## Metodo di invio consigliato
Il metodo più affidabile con questa integrazione è l'utilizzo del servizio generico `notify.send_message`.

### Esempio YAML (Automazioni/Script)
```yaml
action:
  - service: notify.send_message
    target:
      entity_id: notify.cucina_speak
    data:
      message: "Il caffè è pronto!"
```

### Esempio Pyscript
```python
service.call("notify", "send_message", 
             entity_id="notify.cucina_speak", 
             message="Il caffè è pronto!")
```

## Note tecniche
- La piattaforma utilizzata è `alexa_devices` (non la vecchia `alexa_media`).
- Il servizio `cucina_speak` è mappato direttamente come entità di notifica.
- Per gli annunci (che interrompono brevemente la riproduzione su tutti i dispositivi), utilizzare le entità che terminano in `_announce`.
