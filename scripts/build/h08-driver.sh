#!/bin/bash
set -euo pipefail
cd /opt/toddy-build/scripts/build
python3 h08/require_gate.py
prefix=/var/log/toddy/h08-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
set +e
python3 run_step.py h08-base-config h08/base-config.sh h08/base-config-check.sh --user root
result=$?
set -e
echo "$result" > "$prefix.exit"
exit "$result"
