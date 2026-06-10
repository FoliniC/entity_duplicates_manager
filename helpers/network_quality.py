import subprocess
import json
import statistics
import time

HOST = "1.1.1.1"
COUNT = 10

def get_quality():
    try:
        # Run ping command
        # -c count: number of packets
        # -q: quiet output
        # -i 0.2: interval 0.2s (if permitted)
        cmd = ["ping", "-c", str(COUNT), "-i", "0.2", HOST]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        output = result.stdout
        # Example output parts:
        # 10 packets transmitted, 10 received, 0% packet loss, time 1814ms
        # rtt min/avg/max/mdev = 12.345/15.678/20.123/2.456 ms
        
        lines = output.splitlines()
        stats_line = ""
        rtt_line = ""
        rtts = []
        
        # Parse individual RTTs if we can (ping doesn't show them with -q)
        # Re-run without -q to get jitter
        cmd_full = ["ping", "-c", str(COUNT), "-i", "0.2", HOST]
        result_full = subprocess.run(cmd_full, capture_output=True, text=True)
        
        for line in result_full.stdout.splitlines():
            if "time=" in line:
                try:
                    rtt = float(line.split("time=")[1].split(" ")[0])
                    rtts.append(rtt)
                except:
                    pass
            if "packets transmitted" in line:
                stats_line = line
            if "rtt min/avg/max/mdev" in line:
                rtt_line = line

        # Calculate packet loss
        loss = 0
        if "packet loss" in stats_line:
            loss = float(stats_line.split("%")[0].split(",")[-1].strip())

        # Calculate Jitter (standard deviation of RTTs)
        jitter = 0
        if len(rtts) > 1:
            jitter = statistics.stdev(rtts)
        
        # Parse avg RTT
        avg_rtt = 0
        if "/" in rtt_line:
            avg_rtt = float(rtt_line.split("=")[1].split("/")[1])

        return {
            "packet_loss": loss,
            "jitter": round(jitter, 2),
            "ping": round(avg_rtt, 2),
            "status": "online" if loss < 100 else "offline"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

if __name__ == "__main__":
    print(json.dumps(get_quality()))
