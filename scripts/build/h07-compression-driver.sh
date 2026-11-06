#!/bin/bash
# Next five chapter 8 packages only. H07 completion requires all remaining work.
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-xz.success.json ]] || exit 1
for package in lz4 zstd file readline pcre2; do
    if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
    python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
    result=$?
    if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-compression-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-compression-driver.exit
