#!/bin/bash
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-acl.success.json ]] || exit 1
for package in libcap libxcrypt; do
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-security-libraries-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-security-libraries-driver.exit
