"""Stato degli entiti MG4 (piazzale) dal recorder.

Il recorder usa MariaDB (vedi config/recorder.yaml), non il file SQLite
/home-assistant_v2.db (rinominato in
home-assistant_v2.db.UNUSED_stale_sqlite_mariadb_e_attivo).

Da eseguire dentro il container HA:
    docker exec homeassistant python3 /config/check_mg_soc.py
"""

import sys

sys.path.insert(0, "/config")

from ha_db import entities_like, latest_state  # noqa: E402

TARGET = "sensor.piazzale_mg_mg4_electric_state_of_charge"


def main() -> None:
    state = latest_state(TARGET)
    if state is None:
        print(f"{TARGET} NOT found in states table")
    else:
        print(f"Entity: {TARGET}")
        print(f"State: {state}")

    piazzale = entities_like("%piazzale_mg%")
    if piazzale:
        print(f"\nFound {len(piazzale)} piazzale entities in DB:")
        for entity_id in piazzale:
            print(f"  {entity_id}: {latest_state(entity_id)}")
    else:
        print("No piazzale entities in the database at all")

    soc = entities_like("%state_of_charge%")
    if soc:
        print(f"\nEntities with 'state_of_charge':")
        for entity_id in soc:
            print(f"  {entity_id}: {latest_state(entity_id)}")


if __name__ == "__main__":
    main()
