#!/bin/bash
# Complete critical evidence is revalidated by the installer before staging.
set -uo pipefail
cd /opt/toddy-build/scripts/build
if [[ ! -f /var/log/toddy/build/h07-gcc-install.success.json && ! -f /var/log/toddy/build/h07-gcc-install-recovery.success.json ]]; then
 python3 run_step.py h07-gcc-install h07/gcc-install.sh h07/gcc-install-check.sh --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-install-final-compiler-driver.exit; exit "$result"; fi
fi
bash /opt/toddy-build/scripts/build/h07-post-compiler-driver.sh
result=$?
echo "$result" > /var/log/toddy/h07-install-final-compiler-driver.exit
exit "$result"
