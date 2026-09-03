import sqlite3, json, datetime, os

db_path = '/config/home-assistant_v2.db'
if not os.path.exists(db_path):
    print(f"DB NOT FOUND at {db_path}")
    import subprocess
    result = subprocess.run(['find', '/config', '-name', '*.db'], capture_output=True, text=True)
    print("Found DBs:", result.stdout[:500])
    exit(1)

print(f"DB found: {db_path}, size={os.path.getsize(db_path)} bytes")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

entities = [
    'sensor.bitcoin_price_eur',
    'sensor.btc_current_value',
    'sensor.btc_profit_loss',
    'sensor.btc_profit_loss_net',
    'sensor.btc_tax_amount',
]

for entity_id in entities:
    cur.execute("""
        SELECT last_updated_ts, state
        FROM states
        WHERE entity_id = ?
        ORDER BY last_updated_ts DESC
        LIMIT 10
    """, (entity_id,))
    rows = cur.fetchall()
    print(f"\n=== {entity_id} ===")
    if not rows:
        print("  NO DATA")
    else:
        for ts, state in rows:
            dt = datetime.datetime.fromtimestamp(ts)
            print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} | state={state}")

conn.close()
