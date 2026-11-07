#!/bin/bash
# Ordered final Binutils installation and compiler math prerequisites.
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /mnt/lfs/sources/evidence/h07-binutils/classification.json ]] || exit 1
for package in binutils-install gmp mpfr mpc; do
 # gmp-install is the historical partial-build recovery, not a fresh recipe.
 if [[ $package == gmp && -f /var/log/toddy/build/h07-gmp-install.success.json ]]; then continue; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-math-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-math-driver.exit
