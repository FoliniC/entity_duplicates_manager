import sqlite3
conn = sqlite3.connect('/config/home-assistant_v2.db')
cursor = conn.cursor()
cursor.execute("SELECT entity_id, state FROM states WHERE entity_id LIKE 'media_player.%' AND (entity_id LIKE '%cucina%' OR entity_id LIKE '%echo%' OR entity_id LIKE '%sistema%')")
for row in cursor.fetchall():
    print(row[0], ':', row[1])
conn.close()