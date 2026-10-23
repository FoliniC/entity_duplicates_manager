import sqlite3
conn = sqlite3.connect('/config/home-assistant_v2.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print(row[0])
conn.close()