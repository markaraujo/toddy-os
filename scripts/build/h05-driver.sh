#!/bin/bash
# Run only after H04 passes. Every step requires its own tested postcondition.
set -uo pipefail
cd /opt/toddy-build/scripts/build
for prerequisite in binutils gcc headers glibc libstdcxx; do
    [[ -f /var/log/toddy/build/h04-$prerequisite.success.json ]] || { echo 'H04 incomplete'; exit 1; }
done
for package in m4 ncurses bash coreutils diffutils file findutils gawk grep gzip make patch sed tar xz binutils-pass2 gcc-pass2; do
    if [[ -f /var/log/toddy/build/h05-$package.success.json ]]; then
        echo "Already passed: h05-$package; inspect manifests before rebuild"
        continue
    fi
    python3 run_step.py "h05-$package" "h05/$package.sh" "h05/$package-check.sh"
    result=$?
    if [[ $result != 0 ]]; then
        echo "$result" > /var/log/toddy/h05-driver.exit
        exit "$result"
    fi
done
echo 0 > /var/log/toddy/h05-driver.exit
