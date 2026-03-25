#!/bin/bash
set -e

servername="$1"

systemctl stop wg-quick@$servername
