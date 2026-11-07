#!/bin/bash
# Stop before boot-sector writes; inspect kernel/configuration acceptance first.
set -euo pipefail
cd /opt/toddy-build/scripts/build
prefix=/var/log/toddy/h09-kernel-driver
[[ ! -e $prefix.exit && ! -e $prefix.pid ]] || {
    echo 'Preserve and inspect the previous driver attempt before retry' >&2
    exit 1
}
echo $$ > "$prefix.pid"
trap 'result=$?; echo "$result" > "$prefix.exit"' EXIT
python3 h09/require_gate.py
python3 run_step.py h09-kernel h09/kernel.sh h09/kernel-check.sh --user root
python3 run_step.py h09-boot-config h09/boot-config.sh h09/boot-config-check.sh --user root
