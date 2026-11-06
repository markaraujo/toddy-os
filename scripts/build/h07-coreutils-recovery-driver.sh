#!/bin/bash
# Continue remaining frozen utilities only after complete Coreutils acceptance.
set -uo pipefail
prefix=/var/log/toddy/h07-coreutils-recovery-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
cd /opt/toddy-build/scripts/build
python3 run_step.py h07-coreutils-recovery h07/coreutils-resume.sh h07/coreutils-check.sh --user root
result=$?
if [[ $result == 0 ]]; then
 bash /opt/toddy-build/scripts/build/h07-system-utilities-driver.sh
 result=$?
fi
echo "$result" > "$prefix.exit"
exit "$result"
