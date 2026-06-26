"""
GenAI Grounded Generation — Pyscript service layer
==================================================
Exposes the service `pyscript.genai_grounded_ask` which asks a question to the
local GenAI Grounded gateway (Docker sidecar) and stores the full answer in the
state + attributes of `sensor.risposta_google_grounded`.

Why a sensor and not input_text: Home Assistant caps input_text state at 255
chars, but grounded answers are often longer. A sensor can hold a short state
(e.g. the score or "ok") and the FULL answer as an attribute, with no length
limit and full-text search in the UI.

The gateway URL and token live in rest_command.genai_ask (driven by secrets.yaml),
so this service just calls that rest_command and parses the response.

Deploy to: /config/pyscript/genai_grounded.py
"""

import json
import datetime

# Sensor that holds the last grounded answer.
ENTITY = "sensor.risposta_google_grounded"


def _init_sensor():
    """Create the sensor on first load so it always exists."""
    try:
        current = state.get(ENTITY)
    except Exception:
        current = None
    if current is None or current == "":
        state.set(
            ENTITY,
            "in attesa",
            {
                "friendly_name": "Risposta Google Grounded",
                "icon": "mdi:google",
                "risposta": "",
                "fonti": [],
                "grounding_score": None,
                "domanda": "",
                "aggiornato": "",
            },
        )


_init_sensor()


@service
def genai_grounded_ask(question, system="", temperature=None):
    """
    Pone una domanda al gateway GenAI Grounded (grounding Google Search).

    Args:
        question (str): la domanda da porre.
        system (str): istruzione di sistema opzionale (tono/lingua).
        temperature (float): temperatura di campionamento 0-2 (opzionale).

    Salva la risposta completa in sensor.risposta_google_grounded (attributo
    'risposta') e ritorna il dict con i risultati.
    """
    if not question or not str(question).strip():
        log.warning("GenAI Grounded: domanda vuota, ignoro.")
        return {"error": "Domanda vuota"}

    question = str(question).strip()
    log.info(f"GenAI Grounded: domanda ({len(question)} char): {question[:80]}")

    # 1. Chiama il gateway via rest_command (che ha le credenziali).
    call_data = {"prompt": question}
    if system:
        call_data["system"] = str(system)
    if temperature is not None:
        call_data["temperature"] = temperature

    try:
        result = service.call("rest_command", "genai_ask", return_response=True, **call_data)
    except Exception as e:
        log.error(f"GenAI Grounded: errore chiamata rest_command: {e}")
        state.set(ENTITY, "errore", {"friendly_name": "Risposta Google Grounded",
                                      "icon": "mdi:alert", "errore": str(e),
                                      "aggiornato": datetime.datetime.now().isoformat(timespec="seconds")})
        return {"error": str(e)}

    # 2. Parsifica la risposta del gateway.
    data = _parse_rest_result(result)
    if data is None:
        msg = "Risposta gateway non valida o vuota"
        log.error(f"GenAI Grounded: {msg} (raw: {str(result)[:300]})")
        state.set(ENTITY, "errore", {"friendly_name": "Risposta Google Grounded",
                                      "icon": "mdi:alert", "errore": msg,
                                      "raw": str(result)[:500],
                                      "aggiornato": datetime.datetime.now().isoformat(timespec="seconds")})
        return {"error": msg, "raw": str(result)[:500]}

    risposta = str(data.get("answer", "")).strip() or "Nessuna risposta."
    fonti = data.get("web_search_queries") or []
    score = data.get("grounding_score")

    log.info(f"GenAI Grounded: risposta ({len(risposta)} char), fonti={len(fonti)}, score={score}")

    # 3. Stato breve (score o 'ok') + risposta completa negli attributi.
    state_str = "ok" if score is None else f"score {score}"

    # input_text anteprima (255 char) se esiste, per compatibilita' UI.
    try:
        if state.get("input_text.risposta_google_grounded") is not None:
            service.call("input_text", "set_value",
                         entity_id="input_text.risposta_google_grounded",
                         value=risposta[:255])
    except Exception:
        pass

    state.set(
        ENTITY,
        state_str,
        {
            "friendly_name": "Risposta Google Grounded",
            "icon": "mdi:google",
            "risposta": risposta,
            "fonti": fonti,
            "grounding_score": score,
            "domanda": question,
            "aggiornato": datetime.datetime.now().isoformat(timespec="seconds"),
        },
    )

    return {"answer": risposta, "web_search_queries": fonti,
            "grounding_score": score, "domanda": question}


def _parse_rest_result(result):
    """
    rest_command con return_response=True ritorna un dict che puo' contenere:
      - 'json' gia' parsato
      - 'body' (str JSON)
      - 'content' (bytes/str)
      - oppure il dict stesso con i campi diretti.
    Restituisce il dict JSON o None.
    """
    if result is None:
        return None
    # Gia' un dict con i campi attesi.
    if isinstance(result, dict) and ("answer" in result or "candidates" in result):
        return result
    if not isinstance(result, dict):
        return None

    # Chiavi comuni nelle varie versioni di HA.
    for key in ("json", "body", "content", "data", "text"):
        val = result.get(key)
        if val is None:
            continue
        if isinstance(val, dict):
            return val
        if isinstance(val, (bytes, bytearray)):
            val = val.decode("utf-8", "replace")
        if isinstance(val, str):
            val = val.strip()
            if not val:
                continue
            try:
                parsed = json.loads(val)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue
    return None
