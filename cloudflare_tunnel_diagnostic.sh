#!/bin/bash

# Cloudflare Tunnel Diagnostic Script
# Investigation of repeated graceful shutdowns (12-hour period)

CONTAINER_NAME="cloudflare-tunnel"
DIAGNOSTIC_DIR="/tmp/cloudflare_diagnostic_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$DIAGNOSTIC_DIR/diagnostic.log"
mkdir -p "$DIAGNOSTIC_DIR"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

main() {
    log="=== CLOUDFLARE TUNNEL DIAGNOSTIC ==="
    log="Investigation of graceful shutdown patterns"
    log="Duration: 12 hours"
    log="Start Time: $(date)"

    # 1. CONTAINER CONFIGURATION
    log="=== 1. CONTAINER CONFIGURATION ==="
    log="Container status:"
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Name}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | tee -a "$LOG_FILE"

    log="Resource limits:"
    docker inspect "$CONTAINER_NAME" | jq -r '
      .HostConfig | {
        memory: .Memory,
        cpu_shares: .CpuShares,
        cpu_quota: .CpuQuota,
        cpu_period: .CpuPeriod,
        blkio_weight: .BlkioWeight,
        oom_kill_disable: .OomKillDisable,
        pids_limit: .PidsLimit
      } | to_entries | map("\(.key): \(.value)") | join("\n")
    ' 2>/dev/null | tee -a "$LOG_FILE"

    # 2. SYSTEM RESOURCES
    log="=== 2. SYSTEM RESOURCES ==="
    log="System disk usage:"
    df -h | grep -E "^/([^ ]* )" | awk '{print "    " $6 " - " $5}' | tee -a "$LOG_FILE"

    log="System memory:"
    free -h | awk '/^Mem:/ {printf "    Total: %s\n    Used: %s\n    Free: %s\n", $2, $3, $4}' | tee -a "$LOG_FILE"

    # 3. CONNECTIVITY TESTS
    log="=== 3. CONNECTIVITY TESTS ==="
    log="Host external connectivity:"
    curl -I -s --connect-timeout 5 https://home.vialeformica.org | grep -i "HTTP" | tee -a "$LOG_FILE"

    log="Container external connectivity:"
    docker exec "$CONTAINER_NAME" sh -c 'curl -I -s --connect-timeout 5 https://home.vialeformica.org 2>/dev/null' | grep -i "HTTP" | tee -a "$LOG_FILE"

    # 4. LOGGING ANALYSIS
    log="=== 4. LOGGING ANALYSIS ==="
    log="Recent connection patterns (last 2 hours):"
    docker logs "$CONTAINER_NAME" --since "2026-08-17T06:00:0" | grep -E "(Starting tunnel|Initiating graceful shutdown|Connection terminated|failed to dial|timeout)" | tail -20 | tee -a "$LOG_FILE"

    # 5. SHUTDOWN FREQUENCY ANALYSIS
    log="=== 5. SHUTDOWN FREQUENCY ANALYSIS ==="
    declare -i shutdown_count=0
    declare -i start_count=0
    
    while read -r line; do
        if [[ $line == *"Initiating graceful shutdown"* ]]; then
            ((shutdown_count++))
        elif [[ $line == *"Starting tunnel"* ]]; then
            ((start_count++))
        fi
    done < <(docker logs "$CONTAINER_NAME" --since "2026-08-17T06:00:0" | grep -E "(Initiating graceful shutdown|Starting tunnel)")

    log="Shutdown events: $shutdown_count"
    log="Start events: $start_count"
    if [[ $start_count -gt 0 ]]; then
        log="Shutdown-to-start ratio: $(awk "BEGIN {printf \"%.2f\", ($shutdown_count/$start_count)}")"
    fi

    # 6. MONITORING SETUP
    log="=== 6. MONITORING SETUP ==="
    log="Enhanced monitoring script created..."
    
    cat > "$DIAGNOSTIC_DIR/monitor_tunnel.sh" << 'EOF'
#!/bin/bash
CONTAINER_NAME="cloudflare-tunnel"
LOGFILE="$DIAGNOSTIC_DIR/monitor.log"

declare -i monitor_count=0

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Resource monitoring
    echo "$TIMESTAMP - Monitor $monitor_count:" $(docker stats "$CONTAINER_NAME" --no-stream | grep -E "MEM|CPU" | tr '\n' ' ' | sed 's/ *$//') >> "$LOGFILE"
    
    # Connectivity test
    if curl -s --connect-timeout 5 https://home.vialeformica.org >/dev/null 2>&1; then
        echo "$TIMESTAMP - External connectivity: OK" >> "$LOGFILE"
    else
        echo "$TIMESTAMP - External connectivity: FAILED" >> "$LOGFILE"
    fi
    
    monitor_count=$((monitor_count + 1))
    sleep 60
done
EOF

    chmod +x "$DIAGNOSTIC_DIR/monitor_tunnel.sh"
    log="Monitoring script ready at: $DIAGNOSTIC_DIR/monitor_tunnel.sh"

    # 7. SUMMARY AND RECOMMENDATIONS
    log="=== 7. DIAGNOSTIC SUMMARY AND RECOMMENDATIONS ==="
    log="Analysis complete at: $(date)"
    log=""
    log="🔍 KEY FINDINGS:"
    log="1. Container configuration and resource allocation"
    log="2. System resource utilization patterns"
    log="3. Network connectivity verification"
    log="4. Shutdown frequency analysis"
    log="5. Enhanced monitoring capability"
    log=""
    
    if [[ $shutdown_count -gt 3 ]]; then
        log="🚨 CRITICAL: High shutdown frequency detected"
        log="⚠️  RECOMMENDATIONS:"
        log="   • Increase container memory allocation"
        log="   • Implement retry logic with exponential backoff"
        log="   • Monitor for resource constraints"
        log="   • Consider using startup probes"
    else
        log="✅ Shutdown frequency within acceptable range"
        log="⚠️  RECOMMENDATIONS:"
        log="   • Continue monitoring"
        log="   • Implement basic alerting"
    fi

    log=""
    log="📁 DETAILED LOGS:",
    log="   • Main diagnostic: $LOG_FILE"
    log="   • Monitoring log: $DIAGNOSTIC_DIR/monitor.log"
    log="   • Container logs: docker logs $CONTAINER_NAME"
    log=""
    log="✅ DIAGNOSTIC COMPLETED SUCCESSFULLY"
}

# Execute diagnostic
main

# Start monitoring in background
nohup bash "$DIAGNOSTIC_DIR/monitor_tunnel.sh" >/dev/null 2>&1 &

echo "=== CLOUDFLARE TUNNEL DIAGNOSTIC COMPLETE ==="
echo "Results: $LOG_FILE"
echo "Monitoring: $DIAGNOSTIC_DIR/monitor_tunnel.sh"
echo "Status: Running in background"