#!/usr/bin/env python3
"""Manage selective WAN access for Tuya battery sensors on the OpenWrt router."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


CONFIG_DIR = Path(__file__).resolve().parents[1]
CONFIG_ENTRIES = CONFIG_DIR / ".storage" / "core.config_entries"
ROUTER_IP = "192.168.0.11"
ADGUARD_DNS = "192.168.0.3"
SSH_KEY = CONFIG_DIR / ".ssh" / "router_key"
CACHE_FILE = CONFIG_DIR / "temp" / "tuya_selective_isolation_cloud_ips.json"
TABLE = "tuya_block"
CHAIN = "forward"
SELECTIVE_MARKER = "tuya-selective"

TUYA_DOMAINS = [
    "m2.tuyaeu.com",
    "openapi.tuyaeu.com",
    "m3-eu.lifeaiot.com",
    "az.tuyaeu.com",
    "tj.tuyaeu.com",
    "a3.tuyaeu.com",
    "m1.tuyaeu.com",
    "m3.tuyaeu.com",
    "a1.tuyaeu.com",
    "a2.tuyaeu.com",
    "openapi-weaz.tuyaeu.com",
    "a.iot-dns.com",
    "t.iot-dns.com",
]

# Known Tuya cloud IPs seen in drop logs that don't resolve from domains
HARDCODED_TUYA_IPS = [
    "52.28.144.124",
    "3.123.124.46",
]



@dataclass(frozen=True)
class TuyaDevice:
    device_id: str
    name: str
    host: str
    model: str
    product_key: str

    @property
    def is_battery_sensor(self) -> bool:
        text = f"{self.name} {self.model}".lower()
        return (
            self.name.lower().startswith("th")
            or "t&h" in text
            or "t & h" in text
            or "temperature & humidity" in text
            or "temperature humidity" in text
        )


def run_router(cmd: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    full_cmd = [
        "ssh",
        "-F",
        "/dev/null",
        "-i",
        str(SSH_KEY),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        f"root@{ROUTER_IP}",
        cmd,
    ]
    return subprocess.run(
        full_cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def nft(args: str, check: bool = True) -> str:
    return run_router(f"nft {args}", check=check).stdout


def load_tuya_devices() -> list[TuyaDevice]:
    data = json.loads(CONFIG_ENTRIES.read_text())
    devices: list[TuyaDevice] = []
    for entry in data["data"]["entries"]:
        if entry.get("domain") != "localtuya":
            continue
        for device_id, raw in entry.get("data", {}).get("devices", {}).items():
            host = raw.get("host")
            if not host:
                continue
            devices.append(
                TuyaDevice(
                    device_id=device_id,
                    name=raw.get("friendly_name") or raw.get("name") or device_id,
                    host=host,
                    model=raw.get("model") or "",
                    product_key=raw.get("product_key") or "",
                )
            )
    return devices


def valid_domain(domain: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9.-]+", domain):
        raise ValueError(f"Invalid domain: {domain}")
    return domain


def valid_ip(ip: str) -> str:
    return str(ipaddress.ip_address(ip))


def resolve_domains(domains: list[str]) -> dict[str, list[str]]:
    resolved: dict[str, list[str]] = {}
    for domain in domains:
        valid_domain(domain)
        proc = run_router(f"nslookup {domain} {ADGUARD_DNS}", check=False)
        ips = sorted(
            {
                valid_ip(match)
                for match in re.findall(
                    r"Address(?: \d+)?:\s+(\d+\.\d+\.\d+\.\d+)", proc.stdout
                )
                if match != ADGUARD_DNS
            }
        )
        resolved[domain] = ips
    return resolved


def load_recent_cloud_ips(current_ips: set[str], ttl_hours: float) -> list[str]:
    now = time.time()
    ttl_seconds = ttl_hours * 3600
    cache: dict[str, float] = {}
    if CACHE_FILE.exists():
        try:
            raw = json.loads(CACHE_FILE.read_text())
            cache = {valid_ip(ip): float(seen) for ip, seen in raw.items()}
        except (OSError, ValueError, json.JSONDecodeError):
            cache = {}

    cache = {
        ip: seen
        for ip, seen in cache.items()
        if now - seen <= ttl_seconds
    }
    for ip in current_ips:
        cache[valid_ip(ip)] = now

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True))
    return sorted(cache)


def list_chain() -> str:
    return nft(f"-a list chain inet {TABLE} {CHAIN}", check=False)


def list_set(name: str) -> str:
    return nft(f"-a list set inet {TABLE} {name}", check=False)


def parse_set_ips(text: str) -> set[str]:
    return set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text))


def delete_rules_matching(pattern: str) -> list[int]:
    chain = list_chain()
    deleted: list[int] = []
    for line in chain.splitlines():
        if pattern not in line:
            continue
        match = re.search(r"# handle (\d+)", line)
        if not match:
            continue
        handle = int(match.group(1))
        nft(f"delete rule inet {TABLE} {CHAIN} handle {handle}", check=False)
        deleted.append(handle)
    return deleted


def delete_plain_accepts_for_ips(ips: list[str]) -> list[int]:
    chain = list_chain()
    deleted: list[int] = []
    for ip in ips:
        for line in chain.splitlines():
            if SELECTIVE_MARKER in line:
                continue
            if f"ip saddr {ip} accept" not in line:
                continue
            match = re.search(r"# handle (\d+)", line)
            if not match:
                continue
            handle = int(match.group(1))
            nft(f"delete rule inet {TABLE} {CHAIN} handle {handle}", check=False)
            deleted.append(handle)
    return deleted


def ensure_base() -> None:
    nft(f"add table inet {TABLE}", check=False)
    nft(f"add set inet {TABLE} battery_ips '{{ type ipv4_addr ; }}'", check=False)
    nft(f"add set inet {TABLE} allowed_tuya_cloud '{{ type ipv4_addr ; }}'", check=False)
    nft(
        f"add chain inet {TABLE} {CHAIN} "
        "'{ type filter hook forward priority -10 ; policy accept ; }'",
        check=False,
    )


def replace_set(name: str, ips: list[str]) -> None:
    nft(f"flush set inet {TABLE} {name}", check=False)
    if ips:
        elements = ", ".join(valid_ip(ip) for ip in ips)
        nft(f"add element inet {TABLE} {name} '{{ {elements} }}'")


def add_ips_to_set(name: str, ips: list[str]) -> None:
    existing = parse_set_ips(list_set(name))
    for ip in ips:
        if ip not in existing:
            nft(f"add element inet {TABLE} {name} '{{ {valid_ip(ip)} }}'", check=False)


def install_selective_rules() -> None:
    delete_rules_matching(SELECTIVE_MARKER)
    rules = [
        (
            f"insert rule inet {TABLE} {CHAIN} "
            f"ip saddr @battery_ips "
            f"udp dport 53 "
            f'counter accept comment "{SELECTIVE_MARKER}-dns-udp"'
        ),
        (
            f"insert rule inet {TABLE} {CHAIN} "
            f"ip saddr @battery_ips "
            f"tcp dport 53 "
            f'counter accept comment "{SELECTIVE_MARKER}-dns-tcp"'
        ),
        (
            f"insert rule inet {TABLE} {CHAIN} "
            "ip saddr @battery_ips ip daddr @allowed_tuya_cloud "
            "meta l4proto tcp "
            f'tcp dport {{ 80, 443, 8883, 8886 }} counter accept comment "{SELECTIVE_MARKER}-cloud"'
        ),
        (
            f"insert rule inet {TABLE} {CHAIN} "
            f'ip saddr @battery_ips meta l4proto udp udp dport 123 counter accept comment "{SELECTIVE_MARKER}-ntp"'
        ),
    ]
    for rule in reversed(rules):
        nft(rule)


def status(args: argparse.Namespace) -> int:
    devices = load_tuya_devices()
    battery = [device for device in devices if device.is_battery_sensor]
    blocked = parse_set_ips(list_set("blocked_ips"))
    chain = list_chain()
    domains = list(dict.fromkeys([*TUYA_DOMAINS, *args.domain]))
    resolved = resolve_domains(domains)

    print("Battery Tuya sensors:")
    for device in battery:
        marker = "blocked" if device.host in blocked else "not-blocked"
        full_accept = f"ip saddr {device.host} accept" in chain
        suffix = ", full-accept rule present" if full_accept else ""
        print(f"- {device.host:15} {device.name} ({marker}{suffix})")

    print("\nResolved Tuya cloud endpoints via AdGuard:")
    for domain, ips in resolved.items():
        print(f"- {domain}: {', '.join(ips) if ips else 'no IPv4 answer'}")

    return 0


def apply(args: argparse.Namespace) -> int:
    devices = load_tuya_devices()
    battery_ips = sorted({device.host for device in devices if device.is_battery_sensor})
    domains = list(dict.fromkeys([*TUYA_DOMAINS, *args.domain]))
    resolved = resolve_domains(domains)
    current_cloud_ips = {ip for ips in resolved.values() for ip in ips} | set(HARDCODED_TUYA_IPS)
    cloud_ips = load_recent_cloud_ips(current_cloud_ips, args.cache_ttl_hours)

    if not battery_ips:
        print("No battery Tuya sensors found in localtuya config.", file=sys.stderr)
        return 1
    if not cloud_ips:
        print("No Tuya cloud IPs resolved; refusing to install an empty allowlist.", file=sys.stderr)
        return 1

    ensure_base()
    replace_set("battery_ips", battery_ips)
    replace_set("allowed_tuya_cloud", cloud_ips)
    add_ips_to_set("blocked_ips", battery_ips)
    removed_accepts: list[int] = []
    if args.strict_battery:
        removed_accepts = delete_plain_accepts_for_ips(battery_ips)
    install_selective_rules()

    print(f"Battery sensors in policy: {', '.join(battery_ips)}")
    print(f"Allowed Tuya cloud IPs: {', '.join(cloud_ips)}")
    if removed_accepts:
        print(f"Removed full-accept rules for battery sensors: {removed_accepts}")
    if not args.strict_battery:
        print("Note: existing full-accept rules, if present, were left untouched.")
    return 0


def remove(args: argparse.Namespace) -> int:
    deleted = delete_rules_matching(SELECTIVE_MARKER)
    if args.flush_sets:
        nft(f"flush set inet {TABLE} battery_ips", check=False)
        nft(f"flush set inet {TABLE} allowed_tuya_cloud", check=False)
        try:
            CACHE_FILE.unlink()
        except FileNotFoundError:
            pass
    if deleted:
        print(f"Removed selective Tuya rules: {deleted}")
    else:
        print("No selective Tuya rules found.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    status_parser = sub.add_parser("status", help="show current Tuya battery policy")
    status_parser.add_argument("--domain", action="append", default=[])
    status_parser.set_defaults(func=status)

    apply_parser = sub.add_parser("apply", help="install selective Tuya cloud allow rules")
    apply_parser.add_argument("--domain", action="append", default=[])
    apply_parser.add_argument(
        "--strict-battery",
        action="store_true",
        help="remove plain full-accept rules for battery sensors before applying",
    )
    apply_parser.add_argument(
        "--cache-ttl-hours",
        type=float,
        default=24.0,
        help="keep recently resolved Tuya cloud IPs in the allowlist for this many hours",
    )
    apply_parser.set_defaults(func=apply)

    remove_parser = sub.add_parser("remove", help="remove selective Tuya allow rules")
    remove_parser.add_argument(
        "--flush-sets",
        action="store_true",
        help="also empty battery_ips and allowed_tuya_cloud sets",
    )
    remove_parser.set_defaults(func=remove)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
