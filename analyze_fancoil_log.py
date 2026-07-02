#!/usr/bin/env python3
"""
Analyze fancoil_events.log for window open/close events and advice behavior.
"""

import re
from datetime import datetime
from collections import defaultdict

LOG_FILE = "/home/carlo/docker/homeassistant/config/logs/fancoil_events/fancoil_events.log"

# Pattern to extract log entries
LOG_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(.*?)\] \[(.*?)\] (.*)$'
)

def parse_log():
    events = []
    with open(LOG_FILE, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            m = LOG_PATTERN.match(line)
            if m:
                timestamp_str, level, source, message = m.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                events.append({
                    'line': line_num,
                    'timestamp': timestamp,
                    'level': level,
                    'source': source,
                    'message': message
                })
            else:
                # Continuation line
                if events:
                    events[-1]['message'] += '\n' + line
    return events

def analyze_window_events(events):
    """Find window-related events."""
    window_events = []
    for e in events:
        msg = e['message'].lower()
        if any(kw in msg for kw in ['finestra', 'window', 'aperta', 'chiusa', 'consiglio_finestra', 'consiglio finestra']):
            window_events.append(e)
    return window_events

def analyze_room_state_dumps(events):
    """Extract room state dumps to track humidity, delta, etc."""
    room_dumps = defaultdict(list)
    
    for e in events:
        msg = e['message']
        if 'State Dump' in msg:
            # Extract room name - the source field has the room name
            room = e['source']
            # Extract key metrics
            data = {
                'timestamp': e['timestamp'],
                'room': room,
                'raw': msg
            }
            # Extract temperature
            temp_match = re.search(r'Temp=([\d.]+)°C', msg)
            if temp_match:
                data['temp'] = float(temp_match.group(1))
            # Extract humidity
            hum_match = re.search(r'Hum=([\d.]+)%', msg)
            if hum_match:
                data['humidity'] = float(hum_match.group(1))
            # Extract delta
            delta_match = re.search(r'Delta=([\d.]+)°C', msg)
            if delta_match:
                data['delta'] = float(delta_match.group(1))
            # Extract fan speeds
            sw_match = re.search(r'SW=\[([^\]]+)\]', msg)
            if sw_match:
                data['switches'] = sw_match.group(1)
            # Extract target
            target_match = re.search(r'Target=(\w+)', msg)
            if target_match:
                data['target'] = target_match.group(1)
            # Extract hvac mode
            hvac_match = re.search(r'HvacMode=(\w+)', msg)
            if hvac_match:
                data['hvac_mode'] = hvac_match.group(1)
            # Extract stop condition
            stop_match = re.search(r'StopCond=(\w+)', msg)
            if stop_match:
                data['stop_cond'] = stop_match.group(1)
            # Extract system
            sys_match = re.search(r'System=(\w+)', msg)
            if sys_match:
                data['system'] = sys_match.group(1)
            room_dumps[room].append(data)
    return room_dumps

def analyze_windows_opened_closed(room_dumps):
    """Track when rooms show window-like behavior (humidity dropping, etc.)"""
    print("\n=== WINDOW BEHAVIOR ANALYSIS ===")
    for room, dumps in room_dumps.items():
        if not dumps:
            continue
        print(f"\n--- {room} ({len(dumps)} dumps) ---")
        prev_hum = None
        for d in dumps:
            hum = d.get('humidity')
            temp = d.get('temp')
            delta = d.get('delta')
            target = d.get('target')
            hvac = d.get('hvac_mode')
            stop = d.get('stop_cond')
            sys = d.get('system')
            sw = d.get('switches')
            
            hum_change = ""
            if prev_hum is not None and hum is not None:
                diff = hum - prev_hum
                hum_change = f" Δ={diff:+.1f}%"
                if diff < -2:
                    hum_change += " ⬇️ WINDOW OPEN?"
            prev_hum = hum
            
            fans = ""
            if sw:
                fans = f" fans={sw}"
            
            print(f"  {d['timestamp'].strftime('%H:%M:%S')} T={temp}°C RH={hum}% Delta={delta}°C Target={target} HVAC={hvac} Stop={stop} Sys={sys}{fans}{hum_change}")

def check_consiglio_finestra_events(events):
    """Check for consiglio_finestra related logs."""
    print("\n=== CONSIGLIO FINESTRA EVENTS ===")
    for e in events:
        msg = e['message']
        if 'consiglio_finestra' in msg.lower() or 'consiglio finestra' in msg.lower():
            print(f"  {e['timestamp'].strftime('%H:%M:%S')} [{e['level']}] {e['source']}: {msg[:200]}")

def check_persistent_notifications(events):
    """Check for persistent notification events."""
    print("\n=== PERSISTENT NOTIFICATIONS ===")
    for e in events:
        msg = e['message']
        if 'persistent_notification' in msg.lower() or 'notification.create' in msg.lower() or 'notification.dismiss' in msg.lower():
            print(f"  {e['timestamp'].strftime('%H:%M:%S')} [{e['level']}] {e['source']}: {msg[:300]}")

def main():
    print(f"Parsing {LOG_FILE}...")
    events = parse_log()
    print(f"Total events: {len(events)}")
    
    # Room state dumps
    room_dumps = analyze_room_state_dumps(events)
    analyze_windows_opened_closed(room_dumps)
    
    # Window events
    check_consiglio_finestra_events(events)
    check_persistent_notifications(events)

if __name__ == "__main__":
    main()