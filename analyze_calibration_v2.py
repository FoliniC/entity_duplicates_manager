import os
import re
import glob
import datetime
import statistics

# --- Configuration ---
LOG_DIR = 'logs/fancoil_events'
START_TIME = datetime.datetime(2026, 1, 28, 23, 35, 0)
TARGET_ROOMS = ["Cucina", "Camera grande", "Corridoio", "Bagno", "Sala", "Camera"]

# Robust regex to capture Control, Reference and optional KNX
# Example: 2026-01-30 10:51:00 [PERIODIC] [Camera grande] Control=27.0°C, Setpoint=23.0°C, Reference=20.3°C, Humidity=50.0%, KNX=17.2°C
# Updated to make Humidity optional and handle potential N/A
LINE_REGEX = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[PERIODIC\]\s+\[(.*?)\]\s+Control=([\d\.]+|N/A|unknown).*?Reference=([\d\.]+|N/A|unknown)(?:.*?KNX=([\d\.]+|N/A|unknown))?')

def get_relevant_files():
    all_files = glob.glob(os.path.join(LOG_DIR, "fancoil_events*.log"))
    relevant_files = []
    for f in all_files:
        if f.endswith("fancoil_events.log"):
            relevant_files.append(f)
            continue
        try:
            basename = os.path.basename(f)
            ts_str = basename.replace("fancoil_events_", "").replace(".log", "")
            file_dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d_%H%M%S")
            # Include files from the 28th onwards to be safe (rollover data)
            if file_dt >= datetime.datetime(2026, 1, 28):
                relevant_files.append(f)
        except ValueError:
            continue
    return sorted(relevant_files)

def analyze():
    files = get_relevant_files()
    data = {room: {
        'ctrl': [], 'ref': [], 'knx': [], 'ts': []
    } for room in TARGET_ROOMS}
    
    # Mapping for log room names to TARGET_ROOMS
    room_map = {
        "Cucina": "Cucina",
        "Camera grande": "Camera grande",
        "Cameragrande": "Camera grande",
        "Corridoio": "Corridoio",
        "Bagno": "Bagno",
        "Sala": "Sala",
        "Camera": "Camera"
    }

    # Regex for PERIODIC format: ... [PERIODIC] [Room] Control=... Reference=... KNX=...
    PERIODIC_REGEX = re.compile(r'\[PERIODIC\]\s+\[(.*?)\]\s+Control=(.*?)\s*°C.*?Reference=(.*?)\s*°C(?:.*?KNX=(.*?)\s*°C)?')
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if "[PERIODIC]" not in line: continue
                    
                    match = PERIODIC_REGEX.search(line)
                    if not match: continue
                    
                    room_name_raw, ctrl_s, ref_s, knx_s = match.groups()
                    
                    # Extract timestamp from beginning of line
                    ts_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if not ts_match: continue
                    dt = datetime.datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S")
                    if dt < START_TIME: continue

                    # Normalize room name: remove spaces and lowercase
                    norm_name = room_name_raw.replace(" ", "").lower()
                    target_key = None
                    for r in TARGET_ROOMS:
                        if r.replace(" ", "").lower() == norm_name:
                            target_key = r
                            break
                    
                    if not target_key: continue
                    
                    try:
                        # Clean numeric values
                        def to_f(s):
                            if not s: return None
                            s = s.strip()
                            if s in ["N/A", "unknown", "None", ""]: return None
                            # extract only digits and dot
                            m = re.search(r'[\d\.]+', s)
                            return float(m.group(0)) if m else None

                        c, r = to_f(ctrl_s), to_f(ref_s)
                        k = to_f(knx_s) if knx_s else None
                        
                        if c is None or r is None or c == 0: continue
                        
                        data[target_key]['ctrl'].append(c)
                        data[target_key]['ref'].append(r)
                        data[target_key]['knx'].append(k)
                        data[target_key]['ts'].append(dt)
                    except (ValueError, AttributeError):
                        continue
                    
                    try:
                        c, r = float(ctrl_s), float(ref_s)
                        k = float(knx_s) if knx_s else None
                        if c == 0: continue
                        
                        data[target_key]['ctrl'].append(c)
                        data[target_key]['ref'].append(r)
                        data[target_key]['knx'].append(k)
                        data[target_key]['ts'].append(dt)
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    print(f"\nANALISI TARATURA DAL {START_TIME}")
    print("="*80)
    
    for room in TARGET_ROOMS:
        rd = data[room]
        count = len(rd['ctrl'])
        
        if count == 0:
            print(f"\nSTANZA: {room}")
            print(f"  [AVVISO] Nessun campione valido trovato per questa stanza.")
            # Check if there are raw entries but non-numeric
            continue
        
        # Calculation vs Reference (th*)
        ratios_ref = [rd['ref'][i] / rd['ctrl'][i] for i in range(count)]
        offsets_ref = [rd['ref'][i] - rd['ctrl'][i] for i in range(count)]
        
        avg_ratio_ref = statistics.mean(ratios_ref)
        avg_offset_ref = statistics.mean(offsets_ref)
        std_offset_ref = statistics.stdev(offsets_ref) if count > 1 else 0
        
        print(f"\nSTANZA: {room}")
        print(f"  Campioni: {count} ({min(rd['ts'])} -> {max(rd['ts'])})")
        print(f"  --- Riferimento principale (TH*) ---")
        print(f"  SCALING FACTOR: {avg_ratio_ref:.6f}")
        print(f"  Offset Medio:   {avg_offset_ref:+.2f}°C (DevStd: {std_offset_ref:.2f})")
        
        # Calculation vs KNX (if available)
        knx_samples = [i for i, v in enumerate(rd['knx']) if v is not None]
        if knx_samples:
            ratios_knx = [rd['knx'][i] / rd['ctrl'][i] for i in knx_samples]
            offsets_knx = [rd['knx'][i] - rd['ctrl'][i] for i in knx_samples]
            ref_knx_delta = [rd['ref'][i] - rd['knx'][i] for i in knx_samples]
            
            avg_ratio_knx = statistics.mean(ratios_knx)
            avg_offset_knx = statistics.mean(offsets_knx)
            avg_ref_knx_delta = statistics.mean(ref_knx_delta)
            
            print(f"  --- Riferimento KNX ---")
            print(f"  SCALING FACTOR: {avg_ratio_knx:.6f}")
            print(f"  Offset Medio:   {avg_offset_knx:+.2f}°C")
            print(f"  Delta TH*-KNX:  {avg_ref_knx_delta:+.2f}°C (Coerenza Riferimenti)")
            
            if abs(avg_ref_knx_delta) > 1.5:
                print(f"  [AVVISO] Forte discrepanza tra TH* e KNX ({avg_ref_knx_delta:+.2f}°C).")

        if std_offset_ref > 0.6:
            print(f"  [AVVISO] Alta variabilità dello scarto ({std_offset_ref:.2f}). Possibile influenza di carichi termici locali.")

if __name__ == "__main__":
    analyze()
