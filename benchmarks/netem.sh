#!/usr/bin/env bash
##
## EPITECH PROJECT, 2026
## Project - Documentation
## File description:
## Network tests under degraded
## conditions, with netem (Linux)
##

# Usage: benchmarks/netem.sh <r-type_server> [port]
#
# Runs the server and `rtype_bench bandwidth` under three link conditions:
#   baseline  normal loopback
#   lossy     150 ms +- 20 ms delay, 2 % loss, 2 % duplication
#   slow      the same, limited to 40 kbit/s (5 kB/s)
# Set CLIENT_CMD to also run a real client meanwhile, for example
#   CLIENT_CMD="./r-type_client -p 5432"
#
# Only `tc` runs as root (sudo, asked once). netem applies to every local
# connection while the test runs, and is always removed at the end.

set -u

SERVER="$(realpath "${1:?usage: netem.sh <r-type_server> [port]}")"
PORT="${2:-5432}"
BENCH="$(dirname "$(realpath "$0")")/build/rtype_bench"

cleanup() {
    sudo tc qdisc del dev lo root 2>/dev/null
    pkill -f "^$SERVER" 2>/dev/null
    [ -n "${KEEPALIVE:-}" ] && kill "$KEEPALIVE" 2>/dev/null
    echo "netem removed: $(tc qdisc show dev lo)"
}
trap cleanup EXIT INT TERM

sudo -v || exit 1
( while true; do sudo -n true; sleep 50; done ) 2>/dev/null &
KEEPALIVE=$!

scenario() {
    local name="$1"
    shift
    echo "=== $name ==="
    sudo tc qdisc del dev lo root 2>/dev/null
    [ "$#" -gt 0 ] && sudo tc qdisc add dev lo root netem "$@"
    "$SERVER" --god > "server-$name.log" 2>&1 &
    sleep 1
    [ -n "${CLIENT_CMD:-}" ] && (timeout 30 $CLIENT_CMD > "client-$name.log" 2>&1 &)
    timeout 60 "$BENCH" bandwidth 127.0.0.1 "$PORT" 30
    pkill -f "^$SERVER"
    sleep 1
    echo
}

scenario baseline
scenario lossy delay 150ms 20ms loss 2% duplicate 2%
scenario slow delay 150ms 20ms loss 2% duplicate 2% rate 40kbit
