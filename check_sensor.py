import os
import asyncio
from sqlalchemy import create_engine, text

db_url = 'mariadb+pymysql://homeassistant:P6px8r3YMNyJ3aX9@192.168.0.3:3306/homeassistant'
engine = create_engine(db_url)

with engine.connect() as conn:
    # Check if the sensor has states
    result = conn.execute(text("""
        SELECT s.state, s.last_updated_ts, sm.entity_id
        FROM states s
        JOIN states_meta sm ON s.metadata_id = sm.metadata_id
        WHERE sm.entity_id LIKE '%validated_v3%'
        ORDER BY s.last_updated_ts DESC
        LIMIT 10
    """))
    for row in result:
        print(row)