import re
from datetime import datetime
from collections import defaultdict
import sys
import os

def main():
    """
    Questo script analizza 'climateLog.log' filtrando solo le variazioni 'significative':
    - Cambio velocità ventola target
    - Variazione temperatura >= 0.1°C
    - Cambio setpoint
    
    Utile per stabilire un intervallo di polling (time_pattern) ragionevole.
    """
    log_file = 'climateLog.log'
    if not os.path.exists(log_file):
        print(f"Errore: Il file {log_file} non esiste.")
        return

    print("-" * 60)
    print("Analisi variazioni SIGNIFICATIVE (Temp >= 0.1, Setpoint o Fan)")
    print("-" * 60)

    room_data = defaultdict(list)

    # 2026-01-13 11:50:41 [DEBUG] [Cucina] DEBUG: hvac=heat, temp=21.9°C, sp=22.3°C, mode=heat, diff=0.4°C, fan_hw=low, fan_target=low
    log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) .* \[(.*?)\] DEBUG: hvac=(.*?), temp=(.*?)°C, sp=(.*?)°C, mode=(.*?), diff=(.*?)°C, fan_hw=(.*?), fan_target=(.*)')

    with open(log_file, 'r') as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                timestamp_str, room, hvac, temp, sp, mode, diff, fan_hw, fan_target = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                state = {
                    'temp': float(temp),
                    'sp': float(sp),
                    'fan_target': fan_target.strip()
                }
                room_data[room].append((timestamp, state))

    for room, entries in room_data.items():
        significant_changes = []
        if not entries:
            continue
        
        last_state = None
        for ts, state in entries:
            if last_state is None:
                significant_changes.append(ts)
                last_state = state
                continue
            
            # Significant if fan target changes OR temp changes by more than 0.1 OR setpoint changes
            temp_diff = abs(state['temp'] - last_state['temp'])
            sp_diff = abs(state['sp'] - last_state['sp'])
            fan_changed = state['fan_target'] != last_state['fan_target']
            
            if fan_changed or temp_diff >= 0.099: # 0.099 to avoid float precision issues with 0.1
                significant_changes.append(ts)
                last_state = state
            elif sp_diff >= 0.099:
                significant_changes.append(ts)
                last_state = state
        
        if len(significant_changes) > 1:
            intervals = [(significant_changes[i] - significant_changes[i-1]).total_seconds() for i in range(1, len(significant_changes))]
            avg_interval = sum(intervals) / len(intervals)
            print(f"Room: {room}")
            print(f"  Significant changes detected: {len(significant_changes)}")
            print(f"  Avg time between significant changes: {avg_interval/60:.2f} minutes")
        else:
            print(f"Room: {room}")
            print(f"  Significant changes: {len(significant_changes)} (Troppe poche per una statistica)")

if __name__ == "__main__":
    main()