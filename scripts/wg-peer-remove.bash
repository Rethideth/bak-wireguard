#!/bin/bash  
set -e

INTERFACE="$1"
PEER_KEY="$2"

error() {
    echo "[wg-peer-remove] ERROR: $1" >&2
    exit 1
}

[[ -n "$INTERFACE" ]] || error "Missing interface"
[[ -n "$PEER_KEY" ]] || error "Missing peer public key"

if ! wg set $INTERFACE peer $PEER_KEY remove; then
    error "wg set command failed"
fi

echo "[wg-peer-remove] Peer removed successfully"