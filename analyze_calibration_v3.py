import os
import re
import glob
import datetime
import statistics
import argparse

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, 'logs/fancoil_events')
TARGET_ROOMS = ["Cucina", "Camera grande", "Corridoio", "Bagno", "Sala", "Camera"]

def to_f(s):
    if not s: return None
    s = str(s).strip()
    if s in ["N/A", "unknown", "None", ""]: return None
    # Estrae solo numeri e punti (gestisce '22.0', '22.0°C', ecc.)
    m = re.search(r'([-+]?[\d\.]+)', s)
    return float(m.group(1)) if m else None

def get_relevant_files(start_dt):
    # Usa pattern per includere sia il file corrente che quelli ruotati
    pattern = os.path.join(LOG_DIR, "fancoil_events*.log")
    all_files = glob.glob(pattern)
    relevant_files = []
    
    start_date = start_dt.date()
    
    for f in all_files:
        if f.endswith("fancoil_events.log"):
            relevant_files.append(f)
            continue
            
        # Estrae data dal nome file: fancoil_events_YYYY-MM-DD_HHMMSS.log
        match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(f))
        if match:
            try:
                file_date = datetime.datetime.strptime(match.group(1), "%Y-%m-%d").date()
                if file_date >= start_date:
                    relevant_files.append(f)
            except:
                relevant_files.append(f)
        else:
            # Se non ha una data nel nome ma matcha il pattern, lo includiamo per sicurezza
            relevant_files.append(f)
            
    return sorted(list(set(relevant_files)))

def analyze(start_time_str):
    try:
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    except:
        print(f"ERRORE: Formato data non valido. Usa 'YYYY-MM-DD HH:MM:SS'")
        return

    files = get_relevant_files(start_time)
    print(f"\nANALISI TARATURA DAL {start_time}")
    print(f"File analizzati: {len(files)}")
    print("="*80)
    
    data = {room: {'ctrl': [], 'ref': [], 'knx': [], 'ts': []} for room in TARGET_ROOMS}
    
    # Regex per catturare l'intestazione della riga PERIODIC
    PERIODIC_HEADER = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?\[PERIODIC\]\s+\[(.*?)\]\s+(.*)')

    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    p_match = PERIODIC_HEADER.search(line)
                    if not p_match: continue
                    
                    ts_s, room_raw, content = p_match.groups()
                    dt = datetime.datetime.strptime(ts_s, "%Y-%m-%d %H:%M:%S")
                    if dt < start_time: continue
                    
                    # Normalizzazione nome stanza
                    norm_room = room_raw.replace(" ", "").lower()
                    target_key = next((r for r in TARGET_ROOMS if r.replace(" ", "").lower() == norm_room), None)
                    if not target_key: continue
                    
                    # Estrazione valori singoli (molto più robusta)
                    c_m = re.search(r'Control=([^,°\s]+)', content)
                    r_m = re.search(r'Reference=([^,°\s]+)', content)
                    k_m = re.search(r'KNX=([^,°\s]+)', content)
                    
                    c = to_f(c_m.group(1)) if c_m else None
                    r = to_f(r_m.group(1)) if r_m else None
                    k = to_f(k_m.group(1)) if k_m else None
                    
                    if c is not None and c != 0 and (r is not None or k is not None):
                        data[target_key]['ctrl'].append(c)
                        data[target_key]['ref'].append(r)
                        data[target_key]['knx'].append(k)
                        data[target_key]['ts'].append(dt)
        except Exception as e:
            print(f"Errore nel file {filepath}: {e}")

    for room in TARGET_ROOMS:
        rd = data[room]
        count = len(rd['ctrl'])
        
        print(f"\nSTANZA: {room}")
        if count == 0:
            print(f"  [AVVISO] Nessun campione valido trovato (mancano sia Reference che KNX).")
            continue
            
        print(f"  Campioni totali: {count} ({min(rd['ts'])} -> {max(rd['ts'])})")
        
        # Calcolo vs Reference (TH*) - Filtra i None
        ref_samples = [(rd['ref'][i], rd['ctrl'][i]) for i in range(count) if rd['ref'][i] is not None]
        if ref_samples:
            r_vals, c_vals = zip(*ref_samples)
            ratios_ref = [r_vals[i] / c_vals[i] for i in range(len(r_vals))]
            offsets_ref = [r_vals[i] - c_vals[i] for i in range(len(r_vals))]
            avg_ratio_ref = statistics.mean(ratios_ref)
            avg_offset_ref = statistics.mean(offsets_ref)
            std_offset_ref = statistics.stdev(offsets_ref) if len(offsets_ref) > 1 else 0
            
            print(f"  --- Riferimento principale (TH*) ---")
            print(f"  Campioni TH*: {len(ref_samples)}")
            print(f"  SCALING FACTOR: {avg_ratio_ref:.6f}")
            print(f"  Offset Medio:   {avg_offset_ref:+.2f}°C (DevStd: {std_offset_ref:.2f})")
            if std_offset_ref > 0.6:
                print(f"  [AVVISO] Alta variabilità dello scarto TH* ({std_offset_ref:.2f}).")
        else:
            print(f"  --- Riferimento principale (TH*) ---")
            print(f"  [INFO] Nessun dato disponibile dal sensore TH*.")
        
        # Verifica vs KNX - Filtra i None
        knx_samples_list = [(rd['knx'][i], rd['ctrl'][i], rd['ref'][i]) for i in range(count) if rd['knx'][i] is not None]
        if knx_samples_list:
            k_vals, c_vals_k, r_vals_k = zip(*knx_samples_list)
            ratios_knx = [k_vals[i] / c_vals_k[i] for i in range(len(k_vals))]
            offsets_knx = [k_vals[i] - c_vals_k[i] for i in range(len(k_vals))]
            
            avg_ratio_knx = statistics.mean(ratios_knx)
            avg_offset_knx = statistics.mean(offsets_knx)
            
            print(f"  --- Riferimento KNX ---")
            print(f"  Campioni KNX: {len(knx_samples_list)}")
            print(f"  SCALING FACTOR: {avg_ratio_knx:.6f}")
            print(f"  Offset Medio:   {avg_offset_knx:+.2f}°C")
            
            # Coerenza TH* vs KNX (solo dove entrambi presenti)
            both = [(r, k) for k, c, r in knx_samples_list if r is not None]
            if both:
                ref_vals_b, knx_vals_b = zip(*both)
                deltas = [ref_vals_b[i] - knx_vals_b[i] for i in range(len(ref_vals_b))]
                avg_delta = statistics.mean(deltas)
                std_delta = statistics.stdev(deltas) if len(deltas) > 1 else 0
                print(f"  --- Coerenza Riferimenti (TH* vs KNX) ---")
                print(f"  Delta Medio (TH*-KNX): {avg_delta:+.2f}°C (DevStd: {std_delta:.2f})")
                if std_delta < 0.3:
                    print(f"  [CONSIGLIO] Un offset fisso di {-avg_delta:+.2f}°C su TH* lo allineerebbe al KNX.")
            else:
                print(f"  --- Coerenza Riferimenti (TH* vs KNX) ---")
                print(f"  [INFO] Impossibile confrontare: sensore TH* non disponibile.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analisi taratura fancoil')
    parser.add_argument('start', nargs='?', default='2026-01-28 23:35:00', help='Timestamp inizio (YYYY-MM-DD HH:MM:SS)')
    args = parser.parse_args()
    analyze(args.start)
