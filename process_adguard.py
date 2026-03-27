import json
import csv
import re

def clean_hostname(name):
    if not name:
        return ""
    # Sostituisce spazi e underscore con trattini
    name = re.sub(r'[\s_]+', '-', name)
    # Rimuove caratteri non alfanumerici o trattini
    name = re.sub(r'[^a-zA-Z0-9\-]', '', name)
    # Rimuove trattini doppi o ai bordi
    name = re.sub(r'-+', '-', name).strip('-')
    return name.lower()

# Caricamento dispositivi Tuya
with open('TuyaDevices.json', 'r') as f:
    tuya_data = json.load(f)

devices = tuya_data.get('data', {}).get('devices', {})

# Caricamento dati CSV
mac_map = {}
# C:\\Users\\carlo_2\\OneDrive - Il viale della Formica\\Dati\\Progetti\\Domotica\\HA\\
with open('PortScanner.csv', 'r') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        ip = row.get('ip')
        mac = row.get('mac address')
        csv_name = row.get('nome')
        if ip:
            mac_map[ip] = {
                'mac': mac.lower() if mac else "",
                'csv_name': csv_name
            }

output = []
for dev_id, dev_info in devices.items():
    ip = dev_info.get('host')
    friendly_name = dev_info.get('friendly_name', '')
    
    if ip in mac_map:
        mac = mac_map[ip]['mac']
        
        # Priorità al friendly_name del JSON
        hostname = clean_hostname(friendly_name)
        
        # Se il friendly_name è vuoto o troppo generico, usa il nome del CSV
        if not hostname or hostname == "switch":
            csv_name = mac_map[ip]['csv_name']
            if csv_name and not csv_name.startswith('192-168-'):
                hostname = clean_hostname(csv_name)
            else:
                # Se anche il nome CSV è generico, usa un default o riprova col CSV ripulito
                hostname = clean_hostname(csv_name) if csv_name else f"tuya-{dev_id[:6]}"

        output.append({
            "expires": "",
            "hostname": hostname,
            "ip": ip,
            "mac": mac,
            "static": True
        })

# Ordina per IP per comodità
output.sort(key=lambda x: [int(part) for part in x['ip'].split('.')])
print(json.dumps(output, indent=8))
