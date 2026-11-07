#!/bin/bash
# ADR-0096: build each frozen media dependency once, before first live testing.
set -euo pipefail
cd /opt/toddy-build/scripts/build
prefix=/var/log/toddy/h10-tools-driver
[[ ! -e $prefix.exit && ! -e $prefix.pid ]] || {
    echo 'Inspect and preserve the previous media-tool attempt before retry' >&2
    exit 1
}
echo $$ > "$prefix.pid"
trap 'result=$?; echo "$result" > "$prefix.exit"' EXIT
python3 h10/require_gate.py
python3 run_step.py h10-squashfs-tools h10/squashfs-tools.sh h10/squashfs-tools-check.sh --user root
for component in mtools libburn libisofs libisoburn; do
    python3 run_step.py "h11-$component" "h11/$component.sh" "h11/$component-check.sh" --user root
done
