#!/usr/bin/env bash
# Periodically synchronize the dynamic StreamPack RNDIS alias on Debian.
# Router hotplug owns Router/phone configuration; this host-side companion
# ensures the current <router-usb0>.10 endpoint exists on enp2s0.
set -euo pipefail

LOCK=/tmp/streampack-alias-sync.lock
exec 9>"$LOCK"
flock -n 9 || exit 0

# When the RNDIS device is temporarily absent (for example in Intranet),
# retain the current valid alias and make the periodic timer a successful no-op.
# A failed systemd service is misleading and causes stale aliases to accumulate.
if ! sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh setup_alias; then
  exit 0
fi
