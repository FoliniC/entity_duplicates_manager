"""
Periodic USB Tether Check
Runs every 5 minutes to check router tethering and update input_text entities.
"""
import asyncio
import logging

LOGGER = logging.getLogger(__name__)

@time_trigger("cron(*/5 * * * *)")
async def tether_check():
    """Check router tethering and update HA input_text entities."""
    try:
        # Run the check script on router via SSH
        result = await task.executor(
            ssh_check,
            "/usr/bin/check_and_restore_android_tether.sh"
        )
        
        if result["exit_code"] == 0:
            await input_text.set_value(
                entity_id="input_text.usb_tether_note11_status",
                value="OK - RNDIS attivo, gateway reachable"
            )
            await input_text.set_value(
                entity_id="input_text.usb_tether_android_status",
                value="OK - Tethering ripristinato"
            )
            LOGGER.info("Tether check OK")
        else:
            error_msg = result["stdout"] or result["stderr"] or "timeout/errore"
            await input_text.set_value(
                entity_id="input_text.usb_tether_note11_status",
                value=f"PROBLEMA - {error_msg}"
            )
            await input_text.set_value(
                entity_id="input_text.usb_tether_android_status",
                value=f"PROBLEMA - {error_msg}"
            )
            LOGGER.warning(f"Tether check failed: {error_msg}")
            
    except Exception as e:
        LOGGER.error(f"Tether check error: {e}")
        await input_text.set_value(
            entity_id="input_text.usb_tether_note11_status",
            value=f"ERRORE - {e}"
        )
        await input_text.set_value(
            entity_id="input_text.usb_tether_android_status",
            value=f"ERRORE - {e}"
        )

def ssh_check(script_path):
    """Run SSH command on router."""
    import subprocess
    try:
        cmd = [
            "ssh",
            "-i", "/config/.ssh/router_key",
            "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no",
            "-o", "LogLevel=ERROR",
            "root@192.168.0.11",
            script_path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "timeout"}
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}