#!/usr/bin/env bash
# Forced SSH command for the OpenWrt StreamPack hotplug handler.
# It accepts exactly: setup_alias <IPv4>, then delegates the privileged alias
# update to the existing, sudo-scoped usb_tether.sh command.
set -euo pipefail

command=${SSH_ORIGINAL_COMMAND:-}
if [[ ! $command =~ ^setup_alias[[:space:]]+(([0-9]{1,3}\.){3}[0-9]{1,3})$ ]]; then
  echo "invalid StreamPack alias sync command" >&2
  exit 64
fi

alias_ip=${BASH_REMATCH[1]}
IFS=. read -r o1 o2 o3 o4 <<<"$alias_ip"
for octet in "$o1" "$o2" "$o3" "$o4"; do
  (( 10#$octet <= 255 )) || { echo "invalid StreamPack alias" >&2; exit 64; }
done

exec sudo /home/carlo/docker/homeassistant/config/host_scripts/usb_tether.sh setup_alias "$alias_ip"
