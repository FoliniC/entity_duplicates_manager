import re
from datetime import datetime
from collections import defaultdict
import sys
import os

def main():
    """
    Questo script analizza 'climateLog.log' per calcolare la frequenza di aggiornamento
    di ogni stanza, rilevando qualsiasi cambiamento nelle stringhe di DEBUG.
    Utile per capire quanto spesso le automazioni vengono triggerate inutilmente.
    """
    log_file = 'climateLog.log'
    if not os.path.exists(log_file):
        print(f"Errore: Il file {log_file} non esiste.")
        return

    print("-" * 60)
    print("Analisi frequenza log climateLog.log (qualsiasi variazione)")
    print("-" * 60)

    room_data = defaultdict(list)

    # Regex to extract date, time, room, and state data
    # Format: 2026-01-13 11:50:41 [DEBUG] [Cucina] DEBUG: hvac=heat, temp=21.9°C, sp=22.3°C, mode=heat, diff=0.4°C, fan_hw=low, fan_target=low
    log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) .* \[(.*?)\] DEBUG: (.*)')

    with open(log_file, 'r') as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                timestamp_str, room, state_str = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                room_data[room].append((timestamp, state_str))

    for room, entries in room_data.items():
        changes = []
        if not entries:
            continue
        
        last_state = None
        for ts, state in entries:
            if state != last_state:
                changes.append(ts)
                last_state = state
        
        if len(changes) > 1:
            intervals = [(changes[i] - changes[i-1]).total_seconds() for i in range(1, len(changes))]
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            print(f"Room: {room}")
            print(f"  Total log entries: {len(entries)}")
            print(f"  Total changes detected: {len(changes)}")
            print(f"  Average time between changes: {avg_interval/60:.2f} minutes")
            print(f"  Minimum time between changes: {min_interval/60:.2f} minutes")
            print(f"  Maximum time between changes: {max_interval/60:.2f} minutes")
        else:
            print(f"Room: {room}")
            print(f"  Total log entries: {len(entries)}")
            print(f"  Changes detected: {len(changes)} (Not enough to calculate frequency)")

if __name__ == "__main__":
    main()