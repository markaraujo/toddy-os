#!/bin/bash
# First native test-tool prerequisites; H07 remains incomplete afterward.
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-pcre2.success.json ]] || exit 1
for package in m4 bc flex tcl; do
    if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
    python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
    result=$?
    if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-test-tools-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-test-tools-driver.exit
