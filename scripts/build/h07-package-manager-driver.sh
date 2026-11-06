#!/bin/bash
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-libmd.success.json && -f /var/log/toddy/build/h07-gnupg-recovery.success.json ]] || exit 1
prefix=/var/log/toddy/h07-package-manager-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
for package in dpkg berkeley-db; do
 if [[ -f /var/log/toddy/h07-input-handoff.request ]]; then echo 75 > "$prefix.exit"; exit 75; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > "$prefix.exit"; exit "$result"; fi
done
echo 0 > "$prefix.exit"
