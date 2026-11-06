#!/bin/bash
set -uo pipefail
prefix=/var/log/toddy/h07-findutils-recovery-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
cd /opt/toddy-build/scripts/build
python3 run_step.py h07-findutils-recovery h07/findutils-resume.sh h07/findutils-check.sh --user root
result=$?
if [[ $result == 0 ]]; then
 bash /opt/toddy-build/scripts/build/h07-system-utilities-driver.sh
 result=$?
fi
echo "$result" > "$prefix.exit"
exit "$result"
