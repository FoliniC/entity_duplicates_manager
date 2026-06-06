#!/usr/bin/env python3
"""
HA Area & Friendly Name Setter
Assegna aree e nomi amichevoli alle entità via WebSocket API.
Compatibile con Home Assistant 2026.6+

Uso:
  1. export HA_TOKEN="il_tuo_token_qui"
  2. python3 ha_set_areas.py
"""

import asyncio
import json
import os
import sys

# ─── CONFIGURAZIONE ───────────────────────────────────────────────────────────
HA_URL   = os.getenv("HA_URL",   "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN")
# ──────────────────────────────────────────────────────────────────────────────

if not HA_TOKEN:
    print("ERRORE: La variabile d'ambiente HA_TOKEN non è impostata.")
    print("Uso: export HA_TOKEN='tuo_token_qui' && python3 ha_set_areas.py")
    sys.exit(1)

# Aree da creare se non esistono già
AREA_LABELS = ["Cucina", "Camera Grande", "Camera", "Corridoio", "Bagno", "Sala", "Esterno"]

# (entity_id, area_label, friendly_name)
# area_label = "Rimuovi" → area_id viene impostato a None (rimuove l'area)
ENTITIES = [
    ("sensor.th1a_temperature",                  "Cucina",         "Temperatura TH1A"),
    ("sensor.th1a_humidity",                      "Cucina",         "Umidità TH1A"),
    ("sensor.fancoil_cucina_temperature",         "Cucina",         "Temperatura Fancoil Cucina"),
    ("sensor.fancoil_cucina_humidity",            "Cucina",         "Umidità Fancoil Cucina"),
    ("sensor.th2b_temperature",                   "Camera Grande",  "Temperatura TH2B"),
    ("sensor.th2b_humidity",                      "Camera Grande",  "Umidità TH2B"),
    ("sensor.fancoil_camera_grande_temperature",  "Camera Grande",  "Temperatura Fancoil Camera Grande"),
    ("sensor.fancoil_camera_grande_humidity",     "Camera Grande",  "Umidità Fancoil Camera Grande"),
    ("sensor.temperatura_camera_grande",          "Camera Grande",  "Temperatura KNX Camera Grande"),
    ("sensor.th3c_temperature",                   "Camera",         "Temperatura TH3C"),
    ("sensor.th3c_humidity",                      "Camera",         "Umidità TH3C"),
    ("sensor.fancoil_camera_temperature",         "Camera",         "Temperatura Fancoil Camera"),
    ("sensor.fancoil_camera_humidity",            "Camera",         "Umidità Fancoil Camera"),
    ("sensor.temperatura_camera",                 "Camera",         "Temperatura KNX Camera"),
    ("sensor.fancoil_corridoio_temperature",      "Corridoio",      "Temperatura Fancoil Corridoio"),
    ("sensor.fancoil_corridoio_humidity",         "Corridoio",      "Umidità Fancoil Corridoio"),
    ("sensor.fancoil_bagno_temperature",          "Bagno",          "Temperatura Fancoil Bagno"),
    ("sensor.fancoil_bagno_humidity",             "Bagno",          "Umidità Fancoil Bagno"),
    ("sensor.temperatura_bagno",                  "Bagno",          "Temperatura KNX Bagno"),
    ("sensor.fancoil_sala_temperature",           "Sala",           "Temperatura Fancoil Sala"),
    ("sensor.fancoil_sala_humidity",              "Sala",           "Umidità Fancoil Sala"),
    ("sensor.temperatura_sala",                   "Sala",           "Temperatura KNX Sala"),
    ("sensor.th4d_temperature",                   "Esterno",        "Temperatura TH4D"),
    ("sensor.th4d_humidity",                      "Esterno",        "Umidità Esterna"),
]

try:
    import websockets
except ImportError:
    print("Dipendenza mancante. Installa con: pip install websockets")
    sys.exit(1)

async def run():
    ws_url = HA_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
    msg_id = 1

    async def send(ws, payload):
        nonlocal msg_id
        payload["id"] = msg_id
        msg_id += 1
        await ws.send(json.dumps(payload))
        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            if data.get("id") == payload["id"]:
                return data

    print(f"Connessione a {ws_url} ...")
    async with websockets.connect(ws_url) as ws:
        hello = json.loads(await ws.recv())
        assert hello["type"] == "auth_required", f"Atteso auth_required, ricevuto: {hello}"
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        auth_ok = json.loads(await ws.recv())
        if auth_ok.get("type") != "auth_ok":
            print(f"Autenticazione fallita: {auth_ok}")
            return
        print("Autenticazione OK\n")

        # Lista aree esistenti
        areas_resp = await send(ws, {"type": "config/area_registry/list"})
        area_map = {a["name"]: a["area_id"] for a in areas_resp.get("result", [])}

        # Crea aree mancanti
        for label in AREA_LABELS:
            if label not in area_map:
                print(f"  Area '{label}' non trovata, la creo...")
                resp = await send(ws, {"type": "config/area_registry/create", "name": label})
                if resp.get("success"):
                    a = resp["result"]
                    area_map[a["name"]] = a["area_id"]
                    print(f"    Creata: {a['name']}")

        # Aggiorna entità
        for entity_id, area_label, friendly_name in ENTITIES:
            area_id = None if area_label == "Rimuovi" else area_map.get(area_label)
            payload = {
                "type": "config/entity_registry/update",
                "entity_id": entity_id,
                "name": friendly_name,
            }
            if area_label == "Rimuovi":
                payload["area_id"] = None
            elif area_id:
                payload["area_id"] = area_id
            
            resp = await send(ws, payload)
            if resp.get("success"):
                tag = "area rimossa" if area_label == "Rimuovi" else f"-> {area_label}"
                print(f"  OK {entity_id:45s} {tag:15s} | '{friendly_name}'")
            else:
                print(f"  ERR {entity_id}: {resp.get('error', resp)}")

if __name__ == "__main__":
    asyncio.run(run())
