import sqlite3, json

try:
    conn = sqlite3.connect("/config/home-assistant_v2.db")
    cursor = conn.cursor()
    
    # Check specific entity
    cursor.execute("SELECT entity_id, state FROM states WHERE entity_id = ? ORDER BY last_updated DESC LIMIT 1", 
                   ("sensor.piazzale_mg_mg4_electric_state_of_charge",))
    row = cursor.fetchone()
    if row:
        print(f"Entity: {row[0]}")
        print(f"State: {row[1]}")
    else:
        print("sensor.piazzale_mg_mg4_electric_state_of_charge NOT found in states table")
    
    # Show all piazzale entities
    cursor.execute("SELECT DISTINCT entity_id FROM states WHERE entity_id LIKE '%piazzale_mg%'")
    rows = cursor.fetchall()
    if rows:
        print(f"\nFound {len(rows)} piazzale entities in DB:")
        for r in rows:
            cursor.execute("SELECT state FROM states WHERE entity_id = ? ORDER BY last_updated DESC LIMIT 1", (r[0],))
            s = cursor.fetchone()
            print(f"  {r[0]}: {s[0] if s else 'no state'}")
    else:
        print("No piazzale entities in the database at all")
    
    # Also check what entities exist with "state_of_charge" in the name
    cursor.execute("SELECT DISTINCT entity_id FROM states WHERE entity_id LIKE '%state_of_charge%'")
    rows = cursor.fetchall()
    if rows:
        print(f"\nEntities with 'state_of_charge':")
        for r in rows:
            cursor.execute("SELECT state FROM states WHERE entity_id = ? ORDER BY last_updated DESC LIMIT 1", (r[0],))
            s = cursor.fetchone()
            print(f"  {r[0]}: {s[0] if s else 'no state'}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")