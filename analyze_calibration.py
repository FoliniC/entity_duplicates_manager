import os
import re
import glob
import datetime
import statistics

# --- Configuration ---
LOG_DIR = 'logs/fancoil_events'
START_TIME = datetime.datetime(2026, 1, 26, 15, 30, 0)
TARGET_ROOMS = ["Cucina", "Camera grande", "Corridoio", "Bagno"] # "Camera grande" matches the log sample

# Regex to parse the line
# Example: 2026-01-26 16:30:00 [PERIODIC] [Cucina] Control=20.0°C, Setpoint=21.4°C, Reference=21.5°C, Humidity=50.0%
# We'll use a flexible regex for the float values
LINE_REGEX = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[PERIODIC\]\s+\[(.*?)\]\s+Control=([\d\.]+).*?Reference=([\d\.]+)')

def get_relevant_files():
    all_files = glob.glob(os.path.join(LOG_DIR, "fancoil_events*.log"))
    relevant_files = []
    
    for f in all_files:
        # always include current log
        if f.endswith("fancoil_events.log"):
            relevant_files.append(f)
            continue
            
        # Parse timestamp from filename: fancoil_events_YYYY-MM-DD_HHMMSS.log
        try:
            basename = os.path.basename(f)
            # remove prefix and extension
            ts_str = basename.replace("fancoil_events_", "").replace(".log", "")
            # format is YYYY-MM-DD_HHMMSS
            file_dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d_%H%M%S")
            
            # Optimization: If the file started AFTER the start time, include it.
            # If it started BEFORE, it might still contain data (rollover), 
            # but for simplicity and safety given the filenames,
            # we'll include any file from 2026-01-26 onwards.
            if file_dt.year == 2026 and file_dt.month == 1 and file_dt.day >= 26:
                relevant_files.append(f)
        except ValueError:
            continue
            
    return sorted(relevant_files)

def analyze():
    files = get_relevant_files()
    print(f"Processing {len(files)} files: {files}")
    
    data = {room: {'ratios': [], 'offsets': [], 'timestamps': []} for room in TARGET_ROOMS}
    
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if "[PERIODIC]" not in line:
                        continue
                        
                    match = LINE_REGEX.search(line)
                    if not match:
                        continue
                        
                    dt_str, room, ctrl_str, ref_str = match.groups()
                    
                    # Clean up room name case if needed (log usually has standardized names)
                    # The log sample showed "Camera grande" (lowercase g)
                    # User asked for "Camera Grande", checking case-insensitivity or exact mapping
                    target_key = None
                    for r in TARGET_ROOMS:
                        if r.lower() == room.lower():
                            target_key = r
                            break
                    
                    if not target_key:
                        continue
                        
                    try:
                        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue
                        
                    if dt < START_TIME:
                        continue
                        
                    try:
                        ctrl_val = float(ctrl_str)
                        ref_val = float(ref_str)
                    except ValueError:
                        continue
                        
                    if ctrl_val == 0:
                        continue # Avoid division by zero
                        
                    ratio = ref_val / ctrl_val
                    offset = ref_val - ctrl_val
                    
                    data[target_key]['ratios'].append(ratio)
                    data[target_key]['offsets'].append(offset)
                    data[target_key]['timestamps'].append(dt)
                    
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    # --- Report ---
    print("\n" + "="*60)
    print(f"CALIBRATION ANALYSIS REPORT (Data since {START_TIME})")
    print("="*60)
    
    for room in TARGET_ROOMS:
        room_data = data[room]
        count = len(room_data['ratios'])
        
        if count == 0:
            print(f"\nROOM: {room}")
            print("  No data found matching criteria.")
            continue
            
        ratios = room_data['ratios']
        offsets = room_data['offsets']
        
        avg_ratio = statistics.mean(ratios)
        avg_offset = statistics.mean(offsets)
        
        if count > 1:
            stdev_ratio = statistics.stdev(ratios)
            stdev_offset = statistics.stdev(offsets)
            min_offset = min(offsets)
            max_offset = max(offsets)
        else:
            stdev_ratio = 0.0
            stdev_offset = 0.0
            min_offset = offsets[0]
            max_offset = offsets[0]
            
        print(f"\nROOM: {room}")
        print(f"  Samples: {count}")
        print(f"  Time Range: {min(room_data['timestamps'])} to {max(room_data['timestamps'])}")
        print(f"  Recommended Scaling Factor: {avg_ratio:.6f}")
        print(f"  Average Offset (Ref - Ctrl): {avg_offset:.2f}°C")
        print(f"  Offset Range: [{min_offset:.2f}°C, {max_offset:.2f}°C]")
        print(f"  StdDev (Ratio): {stdev_ratio:.5f}")
        
        # Anomaly Detection
        if stdev_offset > 0.5:
            print("  [WARNING] High variance in offset detected (>0.5°C). Check for solar gain or drafts.")
        if count < 10:
             print("  [WARNING] Very few samples (<10). Result might be unreliable.")

if __name__ == "__main__":
    analyze()
