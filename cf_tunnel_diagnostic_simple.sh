#!/bin/bash

# Simple Cloudflare Tunnel Diagnostic
# Quick investigation of tunnel status and recent activity

CONTAINER_NAME="cloudflare-tunnel"
DIAG_DIR="/tmp/cf_diag_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DIAG_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$DIAG_DIR/diagnostic.log"
}

log "=== CLOUDFLARE TUNNEL DIAGNOSTIC ==="
log "Investigation of tunnel health and stability"

# 1. Current container status
log "=== CURRENT CONTAINER STATUS ==="
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" >> "$DIAG_DIR/status.txt" 2>/dev/null

# 2. Resource limits
log "=== RESOURCE LIMITS ==="
docker inspect "$CONTAINER_NAME" | jq -r '.HostConfig | {memory: .Memory, cpu_shares: .CpuShares, cpu_quota: .CpuQuota}' >> "$DIAG_DIR/resources.json" 2>/dev/null

# 3. System resources
log "=== SYSTEM RESOURCES ==="
df -h | grep -E "^/" | awk '{print $6" - "$5}' >> "$DIAG_DIR/system_resources.txt"

free -h | grep Mem | awk '{print "Memory: " $2" Used: "$3" Free: "$4}' >> "$DIAG_DIR/system_resources.txt"

# 4. Connectivity test
log "=== CONNECTIVITY TEST ==="
if curl -s --connect-timeout 5 https://home.vialeformica.org > /dev/null; then
    log "External connectivity: OK"
else
    log "External connectivity: FAILED"
fi

# 5. Recent tunnel events (last 2 hours)
log "=== RECENT TUNNEL EVENTS (Last 2 Hours) ==="

# Get events from last 2 hours
since_2h=$(date -d "2 hours ago" '+%Y-%m-%dT%H:%M:%S')
docker logs "$CONTAINER_NAME" --since "$since_2h" | grep -E "(Starting tunnel|Initiating graceful shutdown|Connection terminated|failed to dial|timeout)" | tail -30 >> "$DIAG_DIR/events.log" || log "No events found or error"

# 6. Shutdown frequency analysis
log "=== SHUTDOWN FREQUENCY ANALYSIS ==="

# Extract shutdown and start events
shutdown_count=0
start_count=0

while read -r line; do
    if [[ $line == *"Initiating graceful shutdown"* ]]; then
        ((shutdown_count++))
    elif [[ $line == *"Starting tunnel"* ]]; then
        ((start_count++))
    fi
done < <(docker logs "$CONTAINER_NAME" --since "$since_2h" | grep -E "(Initiating graceful shutdown|Starting tunnel)")

log "Shutdown events: $shutdown_count"
log "Start events: $start_count"
if [[ $start_count -gt 0 ]]; then
    ratio=$(awk "BEGIN {printf \"%.2f\", ($shutdown_count/$start_count)}")
    log "Shutdown-to-start ratio: $ratio"
fi

# 7. Current tunnel status
log "=== CURRENT TUNNEL STATUS ==="
docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" >> "$DIAG_DIR/current_status.txt"

# 8. Recent connectivity test
log "=== RECENT CONNECTIVITY TEST ==="
curl -I -s --connect-timeout 5 https://home.vialeformica.org 2>&1 | grep -i HTTP >> "$DIAG_DIR/recent_connectivity.log"

log "=== DIAGNOSTIC COMPLETED ==="
log "Results saved to: $DIAG_DIR"
log "Main log: $DIAG_DIR/diagnostic.log"
log "Status: Completed"

echo "=== CLOUDFLARE TUNNEL DIAGNOSTIC COMPLETE ==="
echo "Results saved to: $DIAG_DIR"
echo "Status: Completed"
log "=== DIAGNOSTIC COMPLETED ==="