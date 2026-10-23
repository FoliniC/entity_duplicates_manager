"""Stampa gli ultimi stati registrati dal recorder per gli entita BTC.

Il recorder usa MariaDB (vedi config/recorder.yaml), non il file SQLite
/home-assistant_v2.db (rinominato in
home-assistant_v2.db.UNUSED_stale_sqlite_mariadb_e_attivo).

Da eseguire dentro il container HA:
    docker exec homeassistant python3 /config/read_ha_db.py
"""

import datetime
import sys

sys.path.insert(0, "/config")

from ha_db import query_states  # noqa: E402

ENTITIES = [
    "sensor.bitcoin_price_eur",
    "sensor.btc_current_value",
    "sensor.btc_profit_loss",
    "sensor.btc_profit_loss_net",
    "sensor.btc_tax_amount",
]


def main() -> None:
    for entity_id in ENTITIES:
        rows = query_states(entity_id, limit=10)
        print(f"\n=== {entity_id} ===")
        if not rows:
            print("  NO DATA")
            continue
        for ts, state in rows:
            dt = datetime.datetime.fromtimestamp(ts)
            print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S')} | state={state}")


if __name__ == "__main__":
    main()
