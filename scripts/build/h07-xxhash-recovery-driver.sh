#!/bin/bash
set -uo pipefail
prefix=/var/log/toddy/h07-xxhash-recovery-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
cd /opt/toddy-build/scripts/build
if [[ ! -f /var/log/toddy/build/h07-time.success.json ]]; then
 python3 run_step.py h07-time h07/time.sh h07/time-check.sh --user root
 result=$?
else result=0
fi
if [[ $result == 0 ]]; then
 python3 run_step.py h07-xxhash-recovery h07/xxhash-test-resume.sh h07/xxhash-check.sh --user root
 result=$?
fi
if [[ $result == 0 ]]; then
 bash /opt/toddy-build/scripts/build/h07-supplemental-tools-driver.sh
 result=$?
fi
echo "$result" > "$prefix.exit"
exit "$result"
