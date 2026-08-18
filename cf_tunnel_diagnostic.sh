#!/bin/bash

# Simple Cloudflare Tunnel Diagnostic Script

CONTAINER_NAME="cloudflare-tunnel"
DIAGNOSTIC_DIR="/tmp/cloudflare_diagnostic_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$DIAGNOSTIC_DIR/diagnostic.log"
mkdir -p "$DIAGNOSTIC_DIR"

# Function to log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

main() {
    log="=== CLOUDFLARE TUNNEL DIAGNOSTIC ==="
    log="Investigation of tunnel health and recent shutdowns"
    log="Start time: $(date)"

    # 1. Container status
    log="=== CONTAINER STATUS ==="
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" >> "$LOG_FILE"

    # 2. Resource limits
    log="=== RESOURCE LIMITS ==="
    docker inspect "$CONTAINER_NAME" | jq -r '.HostConfig | {memory: .Memory, cpu_shares: .CpuShares, cpu_quota: .CpuQuota}' >> "$LOG_FILE" 2>/dev/null

    # 3. Disk usage
    log="=== SYSTEM DISK USAGE ==="
    df -h | grep -E "^/" | awk '{print $6" - "$5" ("$4")"}' >> "$LOG_FILE"

    # 4. Memory usage
    log="=== SYSTEM MEMORY USAGE ==="
    free -h | grep Mem | awk '{print "Total: "$2" Used: "$3" Free: "$4}' >> "$LOG_FILE"

    # 5. Connectivity test
    log="=== CONNECTIVITY TESTS ==="
    curl -I -s --connect-timeout 5 https://home.vialeformica.org 2>&1 | grep -i HTTP >> "$LOG_FILE"

    # 6. Recent tunnel events (last 2 hours)
    log="=== RECENT TUNNEL EVENTS (Last 2 Hours) ==="
    # Get timestamp for 2 hours ago
    TWO_HOURS_AGO=$(date -d "2 hours ago" '+%Y-%m-%dT%H:%M:%S')
    docker logs "$CONTAINER_NAME" --since "$TWO_HOURS_AGO" | grep -E "(Starting tunnel|Initiating graceful shutdown|Connection terminated|failed to dial|timeout)" | tail -30 >> "$LOG_FILE"

    # 7. Shutdown frequency analysis
    log="=== SHUTDOWN FREQUENCY ANALYSIS ==="
    declare -i shutdown_count=0
    declare -i start_count=0

    while read -r line; do
        if [[ $line == *"Initiating graceful shutdown"* ]]; then
            ((shutdown_count++))
        elif [[ $line == *"Starting tunnel"* ]]; then
            ((start_count++))
        fi
    done < <(docker logs "$CONTAINER_NAME" --since "$TWO_HOURS_AGO" | grep -E "(Initiating graceful shutdown|Starting tunnel)")

    log="Shutdown events: $shutdown_count"
    log="Start events: $start_count"
    if [[ $start_count -gt 0 ]]; then
        log="Shutdown-to-start ratio: $(awk "BEGIN {printf \"%.2f\", ($shutdown_count/$start_count)}")"
    fi

    # 8. Current status
    log="=== CURRENT STATUS ==="
    docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" >> "$LOG_FILE"

    # 9. Recent connectivity test
    curl -I -s --connect-timeout 5 https://home.vialeformica.org 2>&1 | grep -i HTTP >> "$LOG_FILE"

    # 10. Summary
    log="=== DIAGNOSTIC SUMMARY ==="
    log="Analysis completed at: $(date)"
    log="Log file location: $LOG_FILE"
    log="Main diagnostic saved successfully"
}

# Execute diagnostic
main

log="=== CLOUDFLARE TUNNEL DIAGNOSTIC COMPLETED ==="
log="Results saved to: $LOG_FILE"
log="Status: Completed"