#!/bin/bash
# Native test harness prerequisites; the critical final binutils suite is next.
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-tcl.success.json ]] || exit 1
for package in expect dejagnu ninja pkgconf; do
    if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
    python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
    result=$?
    if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-harness-driver.exit; exit "$result"; fi
done
python3 run_step.py h07-binutils-build h07/binutils-build.sh h07/binutils-build-check.sh --user root
result=$?
if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-harness-driver.exit; exit "$result"; fi
echo 0 > /var/log/toddy/h07-harness-driver.exit
