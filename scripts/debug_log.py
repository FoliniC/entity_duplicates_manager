import re

with open('/config/logs/fancoil_events/fancoil_events_2026-10-23_081933.log', 'r') as f:
    content = f.read(10000)
    print('First 10000 chars:')
    print(content[:2000])
    print('---')
    # Search for Corridoio
    matches = re.findall(r'Corridoio.*State Dump', content)
    print(f'Corridoio State Dump matches in first 10000: {len(matches)}')
    if matches:
        # Find first match context
        idx = content.find(matches[0])
        print('Context around first match:')
        print(content[max(0,idx-100):idx+300])