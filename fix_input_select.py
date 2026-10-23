"""LEGACY / OBSOLETO - non eseguire cosi' com'e'.

Script usato una volta per impostare a mano `input_select.selected_vehicle`
= MG4 direttamente nel database del recorder. Non e' piu' necessario: il
valore viene ora gestito da RestoreEntity (vedi memoria di progetto).

Perche' non funziona piu':
  1. Il recorder usa MariaDB (config/recorder.yaml -> db_url mysql://...),
     non il file SQLite /config/home-assistant_v2.db, che e' stato rinominato
     in `home-assistant_v2.db.UNUSED_stale_sqlite_mariadb_e_attivo`.
  2. Lo schema delle tabelle del recorder e' cambiato: in `states` non esiste
     piu' la colonna `entity_id` (gli entity_id stanno in `states_meta`), e
     non esistono piu' le colonne `attributes`, `last_changed`, `last_updated`
     in formato testo. Le query qui sotto usano lo schema vecchio.

Per leggere gli stati dal recorder usa l'helper /config/ha_db.py, che
interroga MariaDB con lo schema corretto:

    docker exec homeassistant python3 /config/read_ha_db.py

Scrivere direttamente nelle tabelle del recorder e' sconsigliato: Home
Assistant le riscrive in continuazione e i valori verrebbero sovrascritti.
"""

import sqlite3
import time

DB_PATH = "/config/home-assistant_v2.db.UNUSED_stale_sqlite_mariadb_e_attivo"

print(__doc__)
print("ATTENZIONE: script legacy basato sul vecchio schema SQLite.")
print("Usare /config/ha_db.py per leggere dal recorder MariaDB.\n")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute(
    "SELECT * FROM states_meta WHERE entity_id = ?",
    ("input_select.selected_vehicle",),
)
print("Meta:", cur.fetchone())
cur.execute(
    "SELECT metadata_id FROM states_meta WHERE entity_id = ?",
    ("input_select.selected_vehicle",),
)
meta_row = cur.fetchone()
meta_id = meta_row[0] if meta_row else 100
if meta_row is None:
    cur.execute("SELECT MAX(metadata_id) FROM states_meta")
    max_id = cur.fetchone()[0] or 0
    new_id = max_id + 1
    meta_id = new_id
    cur.execute(
        "INSERT INTO states_meta (metadata_id, entity_id) VALUES (?, ?)",
        (new_id, "input_select.selected_vehicle"),
    )
    print("Inserted meta", new_id)
cur.execute(
    "SELECT attributes_id FROM states WHERE entity_id = ? LIMIT 1",
    ("sensor.ev_charge_2025_current_soc",),
)
attr_ref = cur.fetchone()
attr_id = attr_ref[0] if attr_ref else 1
print("Attr ref:", attr_id)
cur.execute(
    "SELECT 1 FROM states WHERE entity_id = ?",
    ("input_select.selected_vehicle",),
)
has_state = cur.fetchone()
if has_state:
    cur.execute(
        "UPDATE states SET state = ?, last_changed = datetime('now'), "
        "last_updated = datetime('now') WHERE entity_id = ?",
        ("MG4", "input_select.selected_vehicle"),
    )
    print("Updated state to MG4")
else:
    ts_now = int(time.time())
    cur.execute(
        "INSERT INTO states (entity_id, state, attributes, attributes_id, "
        "last_changed, last_updated, last_changed_ts, last_updated_ts, metadata_id) "
        "VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), ?, ?, ?)",
        (
            "input_select.selected_vehicle",
            "MG4",
            "{}",
            attr_id,
            ts_now,
            ts_now,
            meta_id,
        ),
    )
    print("Inserted state MG4")
conn.commit()
print("Done")
