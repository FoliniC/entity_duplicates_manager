# Tuya Balcone — Intercettazione Cloud Alexa/SmartLife

## Problema
Alexa (via skill SmartLife/Tuya Cloud) accende `switch.luce_balcone_switch_1` → automazione `anti_accensione_balcone` la spegne subito perché:
- `context.user_id=None` e `context.parent_id=None` (identico a pulsante fisico/RF)
- `context.source` **mai popolato** da nessuna integrazione (UI, automazione, fisico, Alexa)

## Soluzione: Correlazione Router-Level

### Architettura
```
Alexa → Tuya Cloud (MQTT TLS 8883, HTTPS 443) → Router OpenWrt (192.168.0.11)
                                                        ↓
                                            nftables logging TUYA-BALCONE-*
                                                        ↓
                    HA Automation trigger → script.anti_accensione_balcone_check
                                                        ↓
                                    SSH atomico: date + uptime + dmesg | grep TUYA-BALCONE
                                                        ↓
                                        Parse timestamp dmesg via uptime router
                                                        ↓
                                    Se traffico < 60s → exit 0 → NON spegnere
```

### Componenti

#### 1. Router (OpenWrt 192.168.0.11)
```bash
# nftables chain inet tuya_block forward
# Regole per IP device 192.168.0.123 (MAC d8:fc:92:16:e0:d4)
# Porte: 443, 8883, 8886, 53, 123
# Prefissi: TUYA-BALCONE-IN/OUT/DNS/NTP
```

#### 2. Script Python: `/config/helpers/check_tuya_balcone_cloud.py`
- **SSH atomico**: singolo comando `date +%s && cat /proc/uptime && dmesg | grep TUYA-BALCONE | tail -100`
- **Timestamp parsing**: `event_time = boot_time + dmesg_uptime` (boot_time = router_now - uptime)
- **Lookback**: 60 secondi (copre keepalive MQTT periodico ~60s)
- **Exit codes**: 0 = traffico recente (Alexa legittima), 1 = nessun traffico (anomalo)

#### 3. Automazione: `/config/automations/anti_accensione_balcone.yaml`
```yaml
trigger:
  - platform: state
    entity_id: switch.luce_balcone_switch_1
    from: "off"
    to: "on"
condition:
  - condition: template
    value_template: "{{ trigger.to_state.context.user_id is none and trigger.to_state.context.parent_id is none }}"
action:
  - service: script.turn_on
    target:
      entity_id: script.anti_accensione_balcone_check
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ not states('script.anti_accensione_balcone_check') }}"
        sequence:
          - service: switch.turn_off
            target:
              entity_id: switch.luce_balcone_switch_1
```

#### 4. Script HA: `/config/yaml_generator/scripts/anti_accensione_balcone_check.yaml`
```yaml
sequence:
  - service: shell_command.check_tuya_balcone_cloud
    response_variable: tuya_check
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ tuya_check.cloud_traffic_recent }}"
        sequence:
          - service: logbook.log
            data:
              name: "Anti-Accensione Balcone"
              message: "Traffico cloud Tuya rilevato (Alexa/SmartLife) -> accensione legittima, NON spengo"
              entity_id: switch.luce_balcone_switch_1
      - conditions:
          - condition: template
            value_template: "{{ not tuya_check.cloud_traffic_recent }}"
        sequence:
          - service: switch.turn_off
            target:
              entity_id: switch.luce_balcone_switch_1
          - service: logbook.log
            data:
              name: "Anti-Accensione Balcone"
              message: "Accensione esterna NON voluta rilevata (nessun traffico cloud Tuya) -> luce spenta automaticamente"
              entity_id: switch.luce_balcone_switch_1
```

## Test Results

| Data/Ora | Trigger | Router Log | Script Result | Luce |
|----------|---------|------------|---------------|------|
| 22:09:33 | Alexa | TUYA-BALCONE-IN 349B (MQTT 8883) | `cloud_traffic_recent: true, 8s` | **ACCESA** ✓ |
| 22:19:11 | Alexa | Traffico presente | Bug timezone (fixato) | SPENTA ✗ |
| 22:29:13 | Alexa | Traffico presente | Script usava logread (non dmesg) | SPENTA ✗ |
| 22:40:50 | Test | Keepalive MQTT | `cloud_traffic_recent: true, 11s` | **ACCESA** ✓ |
| 22:48:51 | Alexa | Handshake MQTT 349B + keepalive | `cloud_traffic_recent: true, 8s, 7 eventi` | **ACCESA** ✓ |

## Bug Fixes Applicati

| Bug | Fix |
|-----|-----|
| `logread` non vede nftables log (sono in `dmesg`) | Cambiato a `dmesg 2>/dev/null \| grep TUYA-BALCONE` |
| Due SSH separati → uptime incoerente | **SSH atomico singolo** per time + uptime + dmesg |
| `tail -100` troncato da output limitato | Aumentato buffer SSH, limitato grep a 100 righe |
| Lookback 30s < keepalive MQTT ~60s | **Lookback 60s** |
| SSH warning "Permanently added" inquina output | `-o UserKnownHostsFile=/dev/null` |

## Log HA Esempio (Successo)
```
2026-10-05 22:48:51 [INFO] Traffico cloud Tuya rilevato (Alexa/SmartLife) -> accensione legittima, NON spengo
2026-10-05 22:48:51 [INFO] Verifica traffico cloud Tuya: {"cloud_traffic_recent": true, "last_event_seconds_ago": 8, "event_count": 7}
2026-10-05 22:48:51 [INFO] Luce balcone ACCESO (era off) — Motivo: Fisico/RF (pulsante o telecomando Tuya) [source= user_id=None parent_id=None]
```

## File Chiave
- `/config/helpers/check_tuya_balcone_cloud.py` — **Core detection logic**
- `/config/automations/anti_accensione_balcone.yaml` — **Automation trigger**
- `/config/yaml_generator/scripts/anti_accensione_balcone_check.yaml` — **Script HA**
- `/config/yaml_generator/shell_command/check_tuya_balcone.yaml` — **Shell command def**
- `/config/yaml_generator/scripts/scripts.yaml` — **Include scripts**

## Note Operative
- Router log persistenza: `dmesg` è kernel ring buffer (non persiste across reboot). `logread` usa syslog (persiste se configurato).
- Device Tuya IP: `192.168.0.123` (static lease consigliato)
- Cloud endpoints osservati: `18.153.6.145:8883` (MQTT), `18.158.227.228:443` (HTTPS)
- Non decifriamo TLS — solo correlazione temporale traffico ↔ stato HA