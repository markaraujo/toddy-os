#!/bin/bash
set -uo pipefail
prefix=/var/log/toddy/h07-systemd-recovery-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
cd /opt/toddy-build/scripts/build
python3 run_step.py h07-systemd-recovery h07/systemd-test-resume.sh h07/systemd-check.sh --user root
result=$?
if [[ $result == 0 ]]; then
 bash /opt/toddy-build/scripts/build/h07-final-services-driver.sh
 result=$?
fi
echo "$result" > "$prefix.exit"
exit "$result"
