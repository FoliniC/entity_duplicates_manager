from datetime import datetime

file_path = "scale_events.log"
events = []

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        if "[accensione]" in line and "Luce: ACCESA" in line:
            try:
                # Example: 2026-02-08 15:16:00
                date_str = line[:19]
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                events.append(dt)
            except Exception:
                continue

# Find clusters (e.g., within 5 minutes)
clusters = []
if events:
    current_cluster = [events[0]]
    for i in range(1, len(events)):
        if (events[i] - events[i-1]).total_seconds() <= 300: # 5 minutes
            current_cluster.append(events[i])
        else:
            if len(current_cluster) > 1:
                clusters.append(current_cluster)
            current_cluster = [events[i]]
    # Find patterns by hour of day
by_hour = {}
for dt in events:
    hour = dt.hour
    if hour not in by_hour:
        by_hour[hour] = []
    by_hour[hour].append(dt)

print("\nEvents grouped by hour of the day:")
for hour in sorted(by_hour.keys()):
    count = len(by_hour[hour])
    if count > 5: # Show hours with significant activity
        print(f"- Hour {hour:02}h: {count} events")
        # Show some examples
        examples = [e.strftime("%Y-%m-%d %H:%M") for e in by_hour[hour][-5:]]
        print(f"  Last 5 examples: {', '.join(examples)}")
