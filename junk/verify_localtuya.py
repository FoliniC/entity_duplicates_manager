import json
import os
import subprocess

config_path = ".storage/core.config_entries"

def ping(ip):
    try:
        subprocess.check_output(["ping", "-c", "1", "-W", "1", ip], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

if not os.path.exists(config_path):
    print("Config entries file not found.")
    exit(1)

with open(config_path, "r") as f:
    data = json.load(f)

print("--- ANALISI DISPOSITIVI LOCALTUYA ---")
for entry in data["data"]["entries"]:
    if entry.get("domain") == "localtuya":
        devices = entry.get("data", {}).get("devices", {})
        for dev_id, dev_config in devices.items():
            name = dev_config.get("friendly_name", dev_id)
            sleep_time = dev_config.get("device_sleep_time", 0)
            host = dev_config.get("host")
            
            status = "UP" if ping(host) else "DOWN"
            
            print(f"\nDispositivo: {name} ({host}) - Stato: {status}")
            if sleep_time > 0:
                print(f"  [!] ERRORE: Sleep Time impostato a {sleep_time}. Dovrebbe essere 0 per dispositivi a rete.")
            
            entities = dev_config.get("entities", [])
            for ent in entities:
                ent_name = ent.get("friendly_name", ent.get("id"))
                d_class = ent.get("device_class")
                s_class = ent.get("state_class")
                unit = ent.get("unit_of_measurement")
                
                if d_class == "energy" and s_class == "measurement":
                    print(f"  [!] ERRORE ENTITÀ: '{ent_name}' (Energy) ha state_class 'measurement' (cambiare in 'total_increasing')")
                if d_class == "voltage" and unit is None:
                    print(f"  [!] ERRORE ENTITÀ: '{ent_name}' (Voltage) non ha unità di misura (impostare 'V')")
