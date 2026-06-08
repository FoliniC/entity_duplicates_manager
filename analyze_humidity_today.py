import re
import datetime
import sys

log_file = 'logs/fancoil_events/fancoil_events.log'
# June 8, 2026 is today in this session
start_time = datetime.datetime(2026, 6, 8, 13, 18)
end_time = datetime.datetime(2026, 6, 8, 14, 30) # Up to 14:26 requested

data = []

# Regex patterns
# 2026-06-08 14:16:42 [INFO] [Cucina] State Dump: Trigger=sensor.fancoil_cucina_temperature_difference (-1.7->-1.5), Temp=22.0°C, KNX=N/A°C, Hum=56.0% (Var: 0.0), Setpoint=23.5°C (Raw: 23.5), MasterSP=23.5°C, Delta=-1.5°C (RawDiff: -1.5), Offset=0.0°C, Target=off, HvacMode=cool, StopCond=True, System=False, PDC_H2O=off, Comm=OK, T_Circ=12.0°C, Main=on, Soglie=[S:-0.8, I:-0.6, L:-0.2, M:0.1, H:0.5], SW=[0,0,0,0]
dump_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] \[(Bagno|Cucina|Sala|Camera|Camera grande|Corridoio)\] State Dump: .* Temp=([\d.]+)°C, .* Hum=([\d.]+)% \(Var: ([^)]+)\), .* T_Circ=([\d.]+)')
snapshot_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[WARNING\].* snapshot=(.*)')

# Extra outdoor temp if logged (sometimes it's in the snapshot or we might find it in other logs)
# sensor.temperatura_strenscia is the outdoor temp

try:
    with open(log_file, 'r') as f:
        for line in f:
            ts_match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if not ts_match:
                continue
            
            ts = datetime.datetime.strptime(ts_match.group(1), '%Y-%m-%d %H:%M:%S')
            if ts < start_time or ts > end_time:
                continue

            m_dump = dump_re.search(line)
            if m_dump:
                ts_str, room, temp, hum, hum_var, t_circ = m_dump.groups()
                data.append({
                    'ts': ts, 
                    'type': 'hum', 
                    'room': room, 
                    'temp': float(temp), 
                    'hum': float(hum), 
                    'hum_var': hum_var,
                    't_circ': float(t_circ)
                })
            
            m_snap = snapshot_re.search(line)
            if m_snap:
                ts_str, snap = m_snap.groups()
                snap_dict = {}
                for item in snap.split('; '):
                    if '=' in item:
                        parts = item.split('=', 1)
                        if len(parts) == 2:
                            k, v = parts
                            snap_dict[k.strip()] = v.strip()
                data.append({'ts': ts, 'type': 'snap', 'snap': snap_dict})

    data.sort(key=lambda x: x['ts'])

    print(f"{'Timestamp':<20} | {'Room':<14} | {'Temp':<5} | {'Hum':<5} | {'Var':<7} | {'T_Circ':<6} | {'PDC':<4} | {'DEUM':<4}")
    print("-" * 100)

    current_snap = {}
    
    # We also want to track the Delta T with outdoor if possible.
    # From automation: |temp_int - temp_ext| > 5
    # Do we have outdoor temp in logs? 
    # Let's see if 't_est' or similar is in snapshots.
    
    for entry in data:
        if entry['type'] == 'snap':
            current_snap = entry['snap']
        elif entry['type'] == 'hum':
            room = entry['room']
            temp = entry['temp']
            hum = entry['hum']
            hum_var = entry['hum_var']
            t_circ = entry['t_circ']
            pdc = current_snap.get('pdc', '?')
            deum = current_snap.get('deum', '?')
            
            # Identify if variance is high (> 2.0 for humidity)
            var_alert = ""
            try:
                if hum_var != "unknown" and float(hum_var) > 2.0:
                    var_alert = " [!] VAR"
            except:
                pass

            print(f"{entry['ts']} | {room:<14} | {temp:>5.1f} | {hum:>5.1f}% | {hum_var:<7} | {t_circ:>6.1f} | {pdc:<4} | {deum:<4}{var_alert}")

except Exception as e:
    print(f"Error: {entry if 'entry' in locals() else 'N/A'}")
    print(f"Error detail: {e}")
    sys.exit(1)
