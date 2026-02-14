#!/bin/bash
set -e

SRC="$1"
DSTFILE="$2"
DST="/etc/wireguard/$DSTFILE.conf"

# Validate input
if [[ ! -f "$SRC" ]]; then
  echo "Source file not found"
  exit 1
fi

sysctl -w net.ipv4.ip_forward=1

install -o root -g root -m 600 "$SRC" "$DST"

systemctl restart wg-quick@$DSTFILE

rm -f "$SRC"
