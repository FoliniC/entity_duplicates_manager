import sqlite3, time
conn = sqlite3.connect('/config/home-assistant_v2.db')
cur = conn.cursor()
cur.execute("SELECT * FROM states_meta WHERE entity_id = ?", ('input_select.selected_vehicle',))
print("Meta:", cur.fetchone())
cur.execute("SELECT metadata_id FROM states_meta WHERE entity_id = ?", ('input_select.selected_vehicle',))
meta_row = cur.fetchone()
meta_id = meta_row[0] if meta_row else 100
if meta_row is None:
    cur.execute("SELECT MAX(metadata_id) FROM states_meta")
    max_id = cur.fetchone()[0] or 0
    new_id = max_id + 1
    meta_id = new_id
    cur.execute("INSERT INTO states_meta (metadata_id, entity_id) VALUES (?, ?)", (new_id, 'input_select.selected_vehicle'))
    print("Inserted meta", new_id)
cur.execute("SELECT attributes_id FROM states WHERE entity_id = ? LIMIT 1", ('sensor.ev_charge_2025_current_soc',))
attr_ref = cur.fetchone()
attr_id = attr_ref[0] if attr_ref else 1
print("Attr ref:", attr_id)
cur.execute("SELECT 1 FROM states WHERE entity_id = ?", ('input_select.selected_vehicle',))
has_state = cur.fetchone()
if has_state:
    cur.execute("UPDATE states SET state = ?, last_changed = datetime('now'), last_updated = datetime('now') WHERE entity_id = ?", ('MG4', 'input_select.selected_vehicle'))
    print("Updated state to MG4")
else:
    ts_now = int(time.time())
    cur.execute("INSERT INTO states (entity_id, state, attributes, attributes_id, last_changed, last_updated, last_changed_ts, last_updated_ts, metadata_id) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), ?, ?, ?)", ('input_select.selected_vehicle', 'MG4', '{}', attr_id, ts_now, ts_now, meta_id))
    print("Inserted state MG4")
conn.commit()
print("Done")
