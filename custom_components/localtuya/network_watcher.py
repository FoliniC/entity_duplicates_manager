"""Network watcher for detecting cloud-only device communication with Tuya Cloud.

This module monitors network traffic on the LAN bridge to detect when cloud-only
devices (sleepy/battery devices) wake up and communicate with Tuya Cloud.
"""

import asyncio
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional
from pathlib import Path

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Router OpenWrt per disabilitare il flow offloading (usato solo dal network watcher)
ROUTER_IP = "192.168.0.11"
ROUTER_SSH_KEY = "/config/.ssh/router_key"


@dataclass
class NetworkEvent:
    """Represents a network event from a cloud-only device."""
    device_id: str
    mac: str
    ip: str
    timestamp: datetime
    event_type: str  # "cloud_connect", "dhcp", "arp"
    destination_ip: str
    destination_port: int
    protocol: str  # "tcp", "udp"
    raw_packet: str


class TuyaNetworkWatcher:
    """Monitors network traffic for cloud-only Tuya devices."""

    # Tuya Cloud endpoints to monitor
    TUYA_CLOUD_PORTS = {8883, 443, 8886, 8884, 8885}
    
    def __init__(
        self,
        hass: HomeAssistant,
        device_macs: dict[str, str],  # device_id -> mac
        callback: Callable[[NetworkEvent], None],
    ):
        """Initialize the network watcher.
        
        Args:
            hass: Home Assistant instance
            device_macs: Mapping of device_id -> MAC address for cloud-only devices
            callback: Async callback to handle detected network events
        """
        self.hass = hass
        self._device_macs = device_macs  # device_id -> mac
        # Support MAC addresses both with and without colons
        self._mac_to_device_id = {}
        for dev_id, mac in device_macs.items():
            clean_mac = mac.lower().replace(":", "").replace("-", "")
            colon_mac = ":".join(clean_mac[i:i+2] for i in range(0, len(clean_mac), 2))
            self._mac_to_device_id[clean_mac] = dev_id
            self._mac_to_device_id[colon_mac] = dev_id
        self._callback = callback
        self._process: Optional[asyncio.subprocess.Process] = None
        self._running = False
        self._tcpdump_task: Optional[asyncio.Task] = None

    def _build_bpf_filter(self) -> str:
        """Build BPF filter for tcpdump to capture traffic from/to registered MACs.
        
        For the specific device BC:35:1E:FF:4A:B9, capture ALL traffic (all ports/protocols).
        For other devices, use the standard Tuya cloud filtering.
        """
        if not self._device_macs:
            return "ether host 00:00:00:00:00:00"  # match nothing
        
        # For BC:35:1E:FF:4A:B9, capture all traffic
        # For all other devices, use Tuya cloud filtering
        filter_parts = []
        
        for mac in self._device_macs.values():
            mac_normalized = mac.lower()
            if mac_normalized == "bc:35:1e:ff:4a:b9":
                # Special case: capture ALL traffic for this device - no port restrictions
                filter_parts.append(f"(ether host {mac})")
            else:
                # Standard Tuya filtering for other devices
                port_filter = " or ".join(f"port {port}" for port in self.TUYA_CLOUD_PORTS)
                other_ports = "udp port 6667 or udp port 6666 or udp port 5353 or udp port 1900 or udp port 123 or arp"
                filter_parts.append(f"(ether host {mac} and ({port_filter} or {other_ports}))")
        
        return " or ".join(filter_parts)

    @staticmethod
    def _router_ssh_base() -> list[str]:
        """Return the base SSH command list to connect to the router."""
        return [
            "ssh",
            "-i", ROUTER_SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            "-o", "ServerAliveInterval=2",
            "-o", "ServerAliveCountMax=1",
            f"root@{ROUTER_IP}",
        ]

    async def _router_run(self, cmd: str) -> tuple[int, str, str]:
        """Run a single command on the router via SSH and return (returncode, stdout, stderr)."""
        try:
            process = await asyncio.create_subprocess_exec(
                *self._router_ssh_base(),
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=8)
            return (
                process.returncode,
                stdout.decode("utf-8", errors="ignore") if stdout else "",
                stderr.decode("utf-8", errors="ignore") if stderr else "",
            )
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout SSH router for command: %s", cmd)
            return -1, "", "Timeout"
        except Exception as e:
            _LOGGER.warning("SSH router error for command %s: %s", cmd, e)
            return -1, "", str(e)

    async def start(self) -> None:
        """Start the network watcher — runs tcpdump on the OpenWrt router via SSH."""
        if self._running:
            _LOGGER.warning("Network watcher already running")
            return

        if not self._device_macs:
            _LOGGER.info("No cloud-only devices registered, skipping network watcher")
            return

        # Check if network watcher is disabled via file
        disable_file = Path("/config/disable_network_watcher")
        if disable_file.is_file():
            _LOGGER.info("Network watcher disabled by presence of %s", disable_file)
            return

        # Disable flow offloading on the router so packets reach the CPU (and tcpdump)
        await self._disable_flow_offloading()

        bpf_filter = self._build_bpf_filter()

        # Build the tcpdump command to run ON THE ROUTER (via SSH pipe).
        # The router's br-lan bridge sees ALL traffic from WiFi and wired LAN devices.
        # -i br-lan : OpenWrt LAN bridge (WiFi + cabled)
        # -nn       : no name/port resolution
        # -e        : print MAC addresses (link-level header)
        # -l        : line-buffered text output (readable by readline())
        # -s 96     : capture only first 96 bytes (enough for Ethernet+IP+TCP headers)
        router_tcpdump_cmd = (
            f"tcpdump -i br-lan -nn -e -l -s 96 '{bpf_filter}'"
        )

        _LOGGER.info(
            "Starting network watcher: SSH to %s, running: %s",
            ROUTER_IP, router_tcpdump_cmd,
        )

        # The SSH process streams tcpdump stdout back to HA — we read it with readline()
        self._process = await asyncio.create_subprocess_exec(
            *self._router_ssh_base(),
            router_tcpdump_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        self._running = True
        self._tcpdump_task = asyncio.create_task(self._read_tcpdump_output())
        _LOGGER.info("Network watcher started (tcpdump on router %s br-lan)", ROUTER_IP)

    async def _disable_flow_offloading(self) -> None:
        """Disable flow offloading on the OpenWrt router so packets reach the CPU for capture.
        
        Only applies settings if they differ from the desired state, to avoid unnecessary
        firewall restarts which cause brief internet interruptions.
        """
        # First, check current settings
        check_commands = [
            "uci get firewall.@defaults[0].flow_offloading",
            "uci get firewall.@defaults[0].flow_offloading_hw",
        ]
        
        needs_change = False
        check_failed = False
        for cmd in check_commands:
            code, stdout, stderr = await self._router_run(cmd)
            if code == 0:
                current_value = stdout.strip()
                if current_value != "0":
                    needs_change = True
                    _LOGGER.debug("Flow offloading setting needs change: %s = %s (want 0)", cmd, current_value)
            else:
                check_failed = True
                _LOGGER.warning(
                    "Could not read current flow offloading setting with command %s: %s",
                    cmd,
                    stderr.strip() if stderr else "unknown error",
                )

        if check_failed:
            _LOGGER.warning(
                "Skipping flow offloading changes because router SSH settings check failed"
            )
            return
        
        if not needs_change:
            _LOGGER.info("Flow offloading already disabled on OpenWrt router, skipping")
            return
            
        _LOGGER.info("Disabling flow offloading on OpenWrt router via SSH...")
        commands = [
            "uci set firewall.@defaults[0].flow_offloading=0",
            "uci set firewall.@defaults[0].flow_offloading_hw=0",
            "uci commit firewall",
            "/etc/init.d/firewall restart",
        ]
        for cmd in commands:
            code, stdout, stderr = await self._router_run(cmd)
            if code != 0:
                _LOGGER.warning("Router command failed: %s — %s", cmd, stderr.strip())
            else:
                _LOGGER.debug("Router command OK: %s", cmd)
        _LOGGER.info("Flow offloading disabled on OpenWrt router")

    async def _read_tcpdump_output(self) -> None:
        """Read and parse tcpdump output."""
        if not self._process or not self._process.stdout:
            return

        # Regex to parse tcpdump output
        # Format: timestamp MAC_src > MAC_dst, ethertype IPv4/IPv6, length: protocol details
        # Example: 22:44:42.010940 bc:35:1e:ff:4a:b9 > ff:ff:ff:ff:ff:ff, ethertype IPv4 (0x0800), length 353: UDP, length 204
        
        # Regex pattern for tcpdump output with -nn -e -v
        # timestamp src_mac > dst_mac, ethertype proto, length: details
        packet_re = re.compile(
            r'(\d{2}:\d{2}:\d{2}\.\d{6})\s+'
            r'([0-9a-f:]{17})\s*>\s*([0-9a-f:]{17}),\s*ethertype\s+(\w+)\s*\((0x[0-9a-f]+)\),\s*length\s+(\d+):\s*(.+)'
        )

        arp_re = re.compile(
            r'(\d{2}:\d{2}:\d{2}\.\d{6})\s+'
            r'([0-9a-f:]{17})\s*>\s*([0-9a-f:]{17}),\s*ethertype\s+ARP\s+\(0x0806\),\s*length\s+(\d+):\s+'
            r'Ethernet\s+\(len\s+\d+\),\s+IPv4\s+\(len\s+\d+\),\s+'
            r'(Request|Reply)\s+who-has\s+([\d.]+)\s+tell\s+([\d.]+)'
        )

        tcp_re = re.compile(
            r'(\d{2}:\d{2}:\d{2}\.\d{6})\s+'
            r'([0-9a-f:]{17})\s*>\s*([0-9a-f:]{17}),\s*ethertype\s+IPv4\s+\(0x0800\),\s*length\s+(\d+):\s+'
            r'\(tos\s+0x[0-9a-f]+,\s*ttl\s+\d+,\s*id\s+\d+,\s*offset\s+\d+,\s*flags\s+\[[^\]]*\],\s*'
            r'proto\s+(TCP|UDP)\s+\((\d+)\),\s*length\s+\d+'
        )

        while self._running and self._process and self._process.stdout:
            try:
                line_bytes = await self._process.stdout.readline()
                if not line_bytes:
                    break
                
                line = line_bytes.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                _LOGGER.debug("[TCPDUMP-RAW] %s", line)

                # Parse the packet
                event = self._parse_packet(line)
                if event:
                    res = self._callback(event)
                    if asyncio.iscoroutine(res):
                        await res

            except asyncio.CancelledError:
                break
            except Exception as e:
                _LOGGER.error("Error reading tcpdump output: %s", e)
                await asyncio.sleep(1)

    def _parse_packet(self, line: str) -> Optional[NetworkEvent]:
        """Parse a tcpdump line into a NetworkEvent."""
        try:
            # Match TCP/UDP packets with MAC addresses
            # Format: timestamp src_mac > dst_mac, ethertype IPv4 (0x0800), length XXX: proto details
            # 16:44:42.010940 bc:35:1e:ff:4a:b9 > a4:2b:b0:de:22:e7, ethertype IPv4 (0x0800), length 353: TCP...
            
            # First, try to match MAC addresses and basic structure
            mac_pattern = r'([0-9a-f:]{17})\s*>\s*([0-9a-f:]{17})'
            mac_match = re.search(mac_pattern, line)
            if not mac_match:
                return None
            
            src_mac = mac_match.group(1).lower()
            dst_mac = mac_match.group(2).lower()
            
            # Check if source or destination MAC matches our monitored devices
            device_id = self._mac_to_device_id.get(src_mac) or self._mac_to_device_id.get(dst_mac)
            if not device_id:
                return None
            
            mac = src_mac if src_mac in self._mac_to_device_id else dst_mac
            
            # Determine event type and extract details
            event_type = "unknown"
            destination_ip = ""
            destination_port = 0
            protocol = "unknown"
            raw_packet = line
            
            # Check for TCP connections to Tuya Cloud ports
            if "proto TCP" in line or "proto TCP" in line or "Flags [S]" in line or "Flags [S.]" in line:
                protocol = "tcp"
                event_type = "cloud_connect"
                # Extract destination IP and port
                ip_port_match = re.search(r'(\d+\.\d+\.\d+\.\d+)\.(\d+)', line)
                if ip_port_match:
                    destination_ip = ip_port_match.group(1)
                    destination_port = int(ip_port_match.group(2))
            
            # Check for UDP to Tuya Cloud ports
            elif "proto UDP" in line or "UDP" in line:
                protocol = "udp"
                port_match = re.search(r'\.(\d+):', line)
                if port_match:
                    port = int(port_match.group(1))
                    if port in {6666, 6667, 6668, 5353, 1900, 53, 123}:
                        destination_port = port
                        if port in {6666, 6667, 6668}:
                            event_type = "tuya_lan_broadcast"
            
            # Check for ARP
            elif "ARP" in line or "arp" in line.lower():
                event_type = "arp"
                protocol = "arp"
            
            # Check for DNS
            elif "port 53" in line or "domain" in line.lower():
                event_type = "dns"
                protocol = "dns"
            
            # Check for TCP to Tuya Cloud ports
            if destination_port in {8883, 443, 8886, 8884, 8885, 8884}:
                event_type = "cloud_connect"
            
            # Extract IPs
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)\.(\d+)', line)
            if ip_match and not destination_ip:
                destination_ip = ip_match.group(1)
                if not destination_port:
                    destination_port = int(ip_match.group(2))
            
            return NetworkEvent(
                device_id=device_id,
                mac=mac,
                ip="",  # Would need more parsing
                timestamp=datetime.now(),
                event_type=event_type,
                destination_ip=destination_ip,
                destination_port=destination_port,
                protocol=protocol,
                raw_packet=line,
            )
        except Exception as e:
            _LOGGER.debug("Failed to parse packet: %s", e)
            return None

    async def stop(self) -> None:
        """Stop the network watcher."""
        self._running = False
        
        if self._tcpdump_task:
            self._tcpdump_task.cancel()
            try:
                await self._tcpdump_task
            except asyncio.CancelledError:
                pass
        
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (ProcessLookupError, asyncio.TimeoutError):
                try:
                    self._process.kill()
                    await self._process.wait()
                except Exception:
                    pass
            self._process = None
        
        _LOGGER.info("Network watcher stopped")


async def create_network_watcher(
    hass: HomeAssistant,
    device_macs: dict[str, str],
    callback: Callable[[NetworkEvent], None],
) -> TuyaNetworkWatcher:
    """Factory function to create and start a network watcher."""
    watcher = TuyaNetworkWatcher(hass, device_macs, callback)
    await watcher.start()
    return watcher
