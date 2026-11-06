#!/bin/bash
# Durable sequential driver; never treat a running dispatcher as completed.
set -uo pipefail
cd /opt/toddy-build/scripts/build
for package in binutils gcc headers glibc libstdcxx; do
    if [[ -f /var/log/toddy/build/h04-$package.success.json ]]; then
        echo "Already passed: h04-$package; inspect manifests before rebuild"
        continue
    fi
    python3 run_step.py "h04-$package" "h04/$package.sh" "h04/$package-check.sh"
    result=$?
    if [[ $result != 0 ]]; then
        echo "$result" > /var/log/toddy/h04-driver.exit
        exit "$result"
    fi
done
echo 0 > /var/log/toddy/h04-driver.exit
