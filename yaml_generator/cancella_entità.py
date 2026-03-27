#!/usr/bin/env python3
import json
import sys


def rimuovi_entita_dal_registry():
    """Rimuove sia 'sensor.consumo_appartamento' che 'sensor.consumo_appartamento_2' dal registry"""

    registry_file = "/usr/share/hassio/homeassistant/.storage/core.entity_registry"
    entities_to_remove = [
        "sensor.consumo_appartamento",
        "sensor.consumo_appartamento_2",
    ]

    try:
        # Leggi il file registry
        print(f"[*] Lettura file registry: {registry_file}")
        with open(registry_file, "r") as f:
            data = json.load(f)

        # Conta le entità prima della rimozione
        entities_before = len(data["data"]["entities"])
        print(f"[*] Entità prima della rimozione: {entities_before}")

        # Stampa le entità correlate a 'consumo_appartamento' (per debug)
        print("\n[*] Entità correlate a 'consumo_appartamento' trovate:")
        for e in data["data"]["entities"]:
            if "consumo_appartamento" in e.get("entity_id", ""):
                unique_id = e.get("unique_id", "N/A")
                disabled = e.get("disabled_by", "no")
                print(f"    - entity_id: {e.get('entity_id')}")
                print(f"      unique_id: {unique_id}")
                print(f"      disabled_by: {disabled}\n")

        # Filtra: rimuovi ENTRAMBE le entità
        original_count = len(data["data"]["entities"])
        data["data"]["entities"] = [
            e
            for e in data["data"]["entities"]
            if e.get("entity_id") not in entities_to_remove
        ]

        # Conta le entità dopo la rimozione
        entities_after = len(data["data"]["entities"])
        removed_count = original_count - entities_after

        if removed_count > 0:
            # Scrivi il file modificato
            print("[*] Scrittura file registry...")
            with open(registry_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[✓] {removed_count} entità rimossa/e")
            print(f"[✓] Entità totali dopo rimozione: {entities_after}")
            print("\n[!] Riavvia Home Assistant per applicare i cambiamenti:")
            print("    sudo systemctl restart homeassistant")
            return 0
        else:
            print("[!] Nessuna entità trovata da rimuovere")
            return 1

    except FileNotFoundError:
        print(f"[✗] Errore: File registry non trovato: {registry_file}")
        print("[!] Assicurati di eseguire lo script con privilegi sudo")
        return 1
    except json.JSONDecodeError as e:
        print(f"[✗] Errore nel parsing JSON: {e}")
        return 1
    except Exception as e:
        print(f"[✗] Errore generico: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = rimuovi_entita_dal_registry()
    sys.exit(exit_code)
