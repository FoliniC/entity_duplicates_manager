"""Helper per interrogare il database del recorder di Home Assistant.

Il recorder usa MariaDB (config/recorder.yaml -> db_url mysql://...), NON il
file SQLite `home-assistant_v2.db` presente in /config, che e' un file
obsoleto/stallo rinominato come
`home-assistant_v2.db.UNUSED_stale_sqlite_mariadb_e_attivo`.

Uso (dentro il container HA, dove mysqlclient e' installato):
    from ha_db import query_states, latest_state, entities_like
    rows = query_states("sensor.th4d_temperature", limit=10)

Nota sullo schema: gli stati stanno in `states`, gli entity_id in
`states_meta`. La query va SEMPRE fatta con il join, non con
`states.entity_id` (che non esiste).
"""

import os
import re
from typing import Any, Optional

RECORDER_YAML = "/config/recorder.yaml"
# Fallback per l'esecuzione fuori dal container.
RECORDER_YAML_HOST = "/home/carlo/docker/homeassistant/config/recorder.yaml"

_STATES_JOIN = """
    FROM states s
    JOIN states_meta sm ON s.metadata_id = sm.metadata_id
"""


def _recorder_yaml_path() -> str:
    for path in (RECORDER_YAML, RECORDER_YAML_HOST):
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        f"recorder.yaml non trovato (cercato in {RECORDER_YAML} e {RECORDER_YAML_HOST})"
    )


def db_url() -> str:
    """Restituisce la db_url del recorder (mariadb:// o mysql://)."""
    with open(_recorder_yaml_path(), encoding="utf-8") as fh:
        for line in fh:
            m = re.search(r"db_url:\s*(\S+)", line)
            if m:
                return m.group(1)
    raise RuntimeError("db_url non trovata in recorder.yaml")


def connect():
    """Apre una connessione al database del recorder (MariaDB).

    Usa mysqlclient (MySQLdb), gia' installato nel container HA.
    """
    import MySQLdb  # import tardivo: non serve se lo script non interroga il DB

    url = db_url()
    m = re.match(r"mysql://([^:]+):([^@]*)@([^:/]+):?(\d*)/(\w+)", url)
    if not m:
        raise RuntimeError(f"db_url non riconosciuta: {url}")
    user, password, host, port, database = m.groups()
    return MySQLdb.connect(
        host=host,
        port=int(port or 3306),
        user=user,
        passwd=password,
        db=database,
        charset="utf8mb4",
    )


def query_states(entity_id: str, limit: int = 10) -> list[tuple[Any, Any]]:
    """Ultimi stati registrati per un entity_id.

    Restituisce una lista di (last_updated_ts, state).
    """
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT s.last_updated_ts, s.state {_STATES_JOIN} "
            "WHERE sm.entity_id = %s "
            "ORDER BY s.last_updated_ts DESC LIMIT %s",
            (entity_id, limit),
        )
        return cur.fetchall()
    finally:
        conn.close()


def latest_state(entity_id: str) -> Optional[Any]:
    """Stato piu' recente per un entity_id, o None se non presente."""
    rows = query_states(entity_id, limit=1)
    return rows[0][1] if rows else None


def entities_like(pattern: str) -> list[str]:
    """Elenco entity_id che corrispondono a un pattern SQL LIKE."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT sm.entity_id "
            "FROM states s JOIN states_meta sm ON s.metadata_id = sm.metadata_id "
            "WHERE sm.entity_id LIKE %s",
            (pattern,),
        )
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
