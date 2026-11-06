#!/bin/bash
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-libxcrypt.success.json ]] || exit 1
for package in shadow gawk; do
 if [[ $package == shadow && -f /var/log/toddy/build/h07-shadow-audit.success.json ]]; then continue; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-accounts-driver.exit; exit "$result"; fi
done
python3 run_step.py h07-gcc-build h07/gcc-build.sh h07/gcc-build-check.sh --user root
result=$?
if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-accounts-driver.exit; exit "$result"; fi
echo 0 > /var/log/toddy/h07-accounts-driver.exit
