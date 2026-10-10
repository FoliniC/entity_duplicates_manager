#!/usr/bin/env python3
"""Check router kernel ring buffer (dmesg) for recent TUYA-BALCONE cloud traffic.

Returns JSON: {"cloud_traffic_recent": bool, "last_event_seconds_ago": int|null}
Exit code: 0 always (state is in JSON output).
"""
import json
import subprocess
import sys

LOOKBACK_SECONDS = 60


def run_ssh(cmd: str) -> tuple[int, str, str]:
    full_cmd = [
        "ssh",
        "-F", "/dev/null",
        "-i", "/config/.ssh/router_key",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        "root@192.168.0.11",
        cmd,
    ]
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=15)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def check_recent_tuya_traffic() -> dict:
    """Check router dmesg for TUYA-BALCONE events in last N seconds.

    Single SSH session to get time, uptime, and dmesg atomically.
    """
    # Single SSH: get time, uptime, AND dmesg in one atomic snapshot
    cmd = "date +%s && cat /proc/uptime && dmesg 2>/dev/null | grep TUYA-BALCONE | tail -100"
    code, stdout, stderr = run_ssh(cmd)
    if code != 0 or not stdout.strip():
        return {"cloud_traffic_recent": False, "last_event_seconds_ago": None, "error": stderr or "no output"}

    lines = stdout.strip().split("\n")
    if len(lines) < 2:
        return {"cloud_traffic_recent": False, "last_event_seconds_ago": None, "error": "insufficient output"}

    router_now = int(lines[0].strip())
    uptime_line = lines[1].strip()
    uptime = float(uptime_line.split()[0])
    boot_time = router_now - uptime

    # Remaining lines are dmesg entries
    dmesg_lines = lines[2:]

    recent_events = []

    for line in dmesg_lines:
        if not line:
            continue
        # Parse dmesg format: "[1005143.076447] TUYA-BALCONE-ININ=..."
        try:
            if not line.startswith("["):
                continue
            end_bracket = line.index("]")
            uptime_str = line[1:end_bracket]
            dmesg_uptime = float(uptime_str)

            # Skip entries from the future (dmesg grew after uptime snapshot)
            if dmesg_uptime > uptime + 1.0:
                continue

            event_time = boot_time + dmesg_uptime
            seconds_ago = router_now - event_time

            if 0 <= seconds_ago <= LOOKBACK_SECONDS:
                recent_events.append(seconds_ago)
        except Exception:
            continue

    if recent_events:
        return {
            "cloud_traffic_recent": True,
            "last_event_seconds_ago": int(min(recent_events)),
            "event_count": len(recent_events)
        }

    return {"cloud_traffic_recent": False, "last_event_seconds_ago": None}


if __name__ == "__main__":
    result = check_recent_tuya_traffic()
    print(json.dumps(result))
    # Sempre exit 0: command_line logga error su exit non-zero.
    # Lo stato è nel JSON (cloud_traffic_recent: true/false).
    sys.exit(0)