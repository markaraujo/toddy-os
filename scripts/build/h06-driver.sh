#!/bin/bash
set -uo pipefail
cd /opt/toddy-build/scripts/build
for package in bootstrap gettext bison perl zlib mpdecimal python texinfo util-linux cleanup; do
    if [[ -f /var/log/toddy/build/h06-$package.success.json ]]; then
        echo "Already passed: h06-$package; inspect before rebuild"
        continue
    fi
    python3 run_step.py "h06-$package" "h06/$package.sh" "h06/$package-check.sh" --user root
    result=$?
    if [[ $result != 0 ]]; then
        echo "$result" > /var/log/toddy/h06-driver.exit
        exit "$result"
    fi
done
echo 0 > /var/log/toddy/h06-driver.exit
