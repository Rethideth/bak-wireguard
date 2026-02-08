#!/bin/bash
set -e

INTERFACE="$1"
PEER_KEY="$2"
ALLOWED_IPS="$3"

error() {
    echo "[wg-peer-add] ERROR: $1" >&2
    exit 1
}

# Validation
[[ -n "$INTERFACE" ]] || error "Missing interface"
[[ -n "$PEER_KEY" ]] || error "Missing peer public key"
[[ -n "$ALLOWED_IPS" ]] || error "Missing allowed IPs"

# Run WireGuard
if ! wg set "$INTERFACE" peer "$PEER_KEY" allowed-ips "$ALLOWED_IPS"; then
    error "wg set command failed"
fi

echo "[wg-peer-add] Peer added successfully"

