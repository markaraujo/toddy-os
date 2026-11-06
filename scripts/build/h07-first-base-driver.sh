#!/bin/bash
# Chapter 8 through Xz only; completion is NOT completion of H07 or G1.
set -uo pipefail
cd /opt/toddy-build/scripts/build
for prerequisite in h06-cleanup h07-man-pages h07-iana-etc h07-glibc-build; do
    [[ -f /var/log/toddy/build/$prerequisite.success.json ]] || { echo "Incomplete prerequisite: $prerequisite"; exit 1; }
done
for package in glibc-install glibc-locales tzdata zlib bzip2 xz; do
    if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then
        echo "Already passed: h07-$package; inspect before rebuild"
        continue
    fi
    python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
    result=$?
    if [[ $result != 0 ]]; then
        echo "$result" > /var/log/toddy/h07-first-base-driver.exit
        exit "$result"
    fi
done
echo 0 > /var/log/toddy/h07-first-base-driver.exit
