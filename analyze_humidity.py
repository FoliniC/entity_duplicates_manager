import re
import datetime
import sys

log_file = 'logs/fancoil_events/fancoil_events.log'
start_time = datetime.datetime(2026, 5, 31, 8, 20)
end_time = datetime.datetime(2026, 5, 31, 18, 0)

data = []

# Regex patterns
dump_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[INFO\] \[(Cucina|Corridoio|Sala)\] State Dump: .* Hum=(\d+)%')
snapshot_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[WARNING\].* snapshot=(.*)')
reset_re = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[WARNING\] \[DEBUG_RESET\] Entity=(.*) changed (on|off) -> (on|off)')

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
                ts_str, room, hum = m_dump.groups()
                data.append({'ts': ts, 'type': 'hum', 'room': room, 'val': int(hum)})
            
            m_snap = snapshot_re.search(line)
            if m_snap:
                ts_str, snap = m_snap.groups()
                # Parse snapshot safely
                snap_dict = {}
                for item in snap.split('; '):
                    if '=' in item:
                        k, v = item.split('=', 1)
                        snap_dict[k] = v
                data.append({'ts': ts, 'type': 'snap', 'snap': snap_dict})

            m_reset = reset_re.search(line)
            if m_reset:
                ts_str, entity, from_s, to_s = m_reset.groups()
                data.append({'ts': ts, 'type': 'reset', 'entity': entity, 'from': from_s, 'to': to_s})

    data.sort(key=lambda x: x['ts'])

    current_snap = {}
    last_hum = {'Cucina': None, 'Corridoio': None, 'Sala': None}

    print(f"{'Timestamp':<20} | {'Room':<10} | {'Hum':<4} | {'PDC':<4} | {'DEUM':<4} | {'POMPA':<4} | {'Event'}")
    print("-" * 80)

    for entry in data:
        if entry['type'] == 'snap':
            current_snap = entry['snap']
        elif entry['type'] == 'reset':
            print(f"{entry['ts']} | {'EVENT':<10} | {'':<4} | {'':<4} | {'':<4} | {'':<4} | {entry['entity']} {entry['from']}->{entry['to']}")
        elif entry['type'] == 'hum':
            room = entry['room']
            val = entry['val']
            pdc = current_snap.get('pdc', '?')
            deum = current_snap.get('deum', '?')
            pompa = current_snap.get('pompa', '?')
            
            # Solo se è cambiato o periodicamente? Stampiamo tutto per ora per vedere il trend.
            print(f"{entry['ts']} | {room:<10} | {val:>3}% | {pdc:<4} | {deum:<4} | {pompa:<4} |")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
