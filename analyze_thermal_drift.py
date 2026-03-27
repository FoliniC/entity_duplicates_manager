import os
import re
import glob
import datetime
import statistics

LOG_DIR = 'logs/fancoil_events'
TARGET_ROOMS = ["Cucina", "Camera grande", "Corridoio", "Bagno"]

# Regex
# 2026-01-26 16:30:00 [PERIODIC] [Cucina] Control=20.0°C, Setpoint=21.4°C, Reference=21.5°C, Humidity=50.0%
PERIODIC_REGEX = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[PERIODIC\]\s+\[(.*?)\]\s+Control=([\d\.]+).*?Reference=([\d\.]+)')

# Regex per rilevare lo stato Main=on/off
# 2026-01-26 16:29:20 [info] [Bagno] State Dump: ... Main=on ...
STATE_REGEX = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?\[(.*?)\]\s+State Dump:.*?Main=(on|off)')

def get_sorted_files():
    # Raccoglie tutti i file di log fancoil
    files = glob.glob(os.path.join(LOG_DIR, "fancoil_events*.log"))
    return sorted(files)

def analyze_drift():
    files = get_sorted_files()
    print(f"Analyzing {len(files)} files for Thermal Drift...")

    # Struttura dati:
    # room_state: { 'state': 'off', 'last_switch_time': datetime }
    # drift_data: { 'Cucina': { 10: [-2, -2.1], 20: [-3.0] ... } } -> bucket temporali di 10 min
    
    room_status = {r: {'state': 'off', 'start_time': None} for r in TARGET_ROOMS}
    drift_stats = {r: {} for r in TARGET_ROOMS}

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # 1. Check State Change
                    state_match = STATE_REGEX.search(line)
                    if state_match:
                        dt_str, room_raw, main_val = state_match.groups()
                        
                        # Normalize room name
                        room = None
                        for r in TARGET_ROOMS:
                            if r.lower() == room_raw.lower():
                                room = r
                                break
                        if not room: continue

                        try:
                            dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                        except: continue

                        current_state = room_status[room]['state']
                        
                        # Se cambia stato
                        if current_state != main_val:
                            room_status[room]['state'] = main_val
                            room_status[room]['start_time'] = dt
                        continue

                    # 2. Check Periodic Data
                    per_match = PERIODIC_REGEX.search(line)
                    if per_match:
                        dt_str, room_raw, ctrl_str, ref_str = per_match.groups()
                        
                        room = None
                        for r in TARGET_ROOMS:
                            if r.lower() == room_raw.lower():
                                room = r
                                break
                        if not room: continue

                        # Analizziamo solo se siamo in stato ON
                        if room_status[room]['state'] != 'on' or room_status[room]['start_time'] is None:
                            continue

                        try:
                            dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                            ctrl_val = float(ctrl_str)
                            ref_val = float(ref_str) # Reference
                        except: 
                            try:
                                # Sometimes ref is passed as 4th group correctly
                                ref_val = float(ref_str)
                            except: continue

                        # Calcolo delta tempo in minuti dall'accensione
                        start_time = room_status[room]['start_time']
                        delta_minutes = (dt - start_time).total_seconds() / 60.0
                        
                        if delta_minutes < 0: continue # Should not happen but safety first
                        if delta_minutes > 180: continue # Ignoriamo cicli troppo lunghi > 3 ore

                        # Errore = Controllo (Tuya) - Riferimento
                        # Esempio: Tuya dice 30, Reale è 20 -> Errore +10
                        error = ctrl_val - ref_val

                        # Bucket ogni 5 minuti
                        bucket = int(delta_minutes // 5) * 5
                        
                        if bucket not in drift_stats[room]:
                            drift_stats[room][bucket] = []
                        drift_stats[room][bucket].append(error)

        except Exception as e:
            # print(f"Skipping error in file {filepath}: {e}")
            pass

    # --- Print Report ---
    print("\n" + "="*80)
    print("ANALISI DERIVA TERMICA (THERMAL DRIFT) - ERRORE vs TEMPO DI ACCENSIONE")
    print("="*80)
    print("Nota: L'errore è (Tuya - Reference). Valori positivi indicano surriscaldamento del sensore.")

    for room in TARGET_ROOMS:
        print(f"\n--- {room.upper()} ---")
        buckets = sorted(drift_stats[room].keys())
        
        if not buckets:
            print("  Nessun dato valido in fase 'ON' trovato.")
            continue

        print(f"  {'Minuti ON':<10} | {'Media Errore':<15} | {'Campioni':<10}")
        print("  " + "-"*40)
        
        for b in buckets:
            vals = drift_stats[room][b]
            avg_err = statistics.mean(vals)
            count = len(vals)
            if count < 5: continue # Filtro rumore
            
            print(f"  {b}-{b+5:<4} min | +{avg_err:5.2f}°C        | {count}")

if __name__ == "__main__":
    analyze_drift()
