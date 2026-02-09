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


install -o root -g root -m 600 "$SRC" "$DST"

systemctl restart wg-quick@$DSTFILE

rm -f "$SRC"