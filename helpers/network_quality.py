import subprocess
import json
import statistics
import time
import sys
import contextlib
import io

HOST = "1.1.1.1"
COUNT = 10

def log_to_halog(level, message):
    try:
        sys.path.append("/config/pyscript/lib")
        with contextlib.redirect_stdout(io.StringIO()):
            import halog2026_lib
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} [{level.upper()}] [network_quality] {message.strip()}\n"
        with contextlib.redirect_stdout(io.StringIO()):
            halog2026_lib.sync_write_log("system", line)
    except Exception as ex:
        # Fallback to stderr so it shows up in Home Assistant main log
        sys.stderr.write(f"[network_quality] Failed to log to HALog2026: {ex}\n")

def get_quality():
    try:
        # Run ping command only once
        cmd = ["ping", "-c", str(COUNT), "-i", "0.2", HOST]
        # Set a reasonable timeout so we never block Home Assistant
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        
        stats_line = ""
        rtt_line = ""
        rtts = []
        
        for line in result.stdout.splitlines():
            if "time=" in line:
                try:
                    rtt = float(line.split("time=")[1].split(" ")[0])
                    rtts.append(rtt)
                except Exception:
                    pass
            if "packets transmitted" in line:
                stats_line = line
            if "min/avg/max" in line:
                rtt_line = line

        # Calculate packet loss
        loss = 0.0
        if stats_line and "packet loss" in stats_line:
            try:
                loss = float(stats_line.split("%")[0].split(",")[-1].strip())
            except Exception:
                pass
        else:
            # Fallback if parsing stats_line failed
            if COUNT > 0:
                loss = ((COUNT - len(rtts)) / COUNT) * 100.0

        # Calculate Jitter (standard deviation of RTTs)
        jitter = 0.0
        if len(rtts) > 1:
            try:
                jitter = statistics.stdev(rtts)
            except Exception:
                pass
        
        # Parse avg RTT
        avg_rtt = 0.0
        if rtt_line and "/" in rtt_line:
            try:
                # E.g. "round-trip min/avg/max = 32.394/35.860/44.698 ms"
                # split on '=': ['round-trip min/avg/max ', ' 32.394/35.860/44.698 ms']
                # split on '/': [' 32.394', '35.860', '44.698 ms']
                avg_rtt = float(rtt_line.split("=")[1].split("/")[1].strip().replace("ms", ""))
            except Exception:
                if rtts:
                    avg_rtt = sum(rtts) / len(rtts)
        else:
            # Fallback to manual average
            if rtts:
                avg_rtt = sum(rtts) / len(rtts)

        status = "online" if loss < 100 else "offline"

        # Log anomalies using HALog2026 system subsystem
        if status == "offline":
            log_to_halog("ERROR", f"Network offline: 100% packet loss to {HOST}")
        elif loss > 10.0:
            log_to_halog("WARNING", f"High packet loss detected: {loss}% loss (ping: {avg_rtt:.1f}ms, jitter: {jitter:.1f}ms)")

        return {
            "packet_loss": round(loss, 2),
            "jitter": round(jitter, 2),
            "ping": round(avg_rtt, 2),
            "status": status
        }
    except subprocess.TimeoutExpired as te:
        error_msg = f"Ping command timed out (expired after 12s)"
        log_to_halog("ERROR", error_msg)
        return {"error": error_msg, "status": "error"}
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        log_to_halog("ERROR", f"Script error: {error_msg}")
        return {"error": error_msg, "status": "error"}

if __name__ == "__main__":
    print(json.dumps(get_quality()))
