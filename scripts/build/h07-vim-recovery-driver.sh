#!/bin/bash
set -uo pipefail
prefix=/var/log/toddy/h07-vim-recovery-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
cd /opt/toddy-build/scripts/build
python3 run_step.py h07-vim-pty-recovery h07/vim-pty-resume.sh h07/vim-check.sh --user root
result=$?
if [[ $result == 0 ]]; then
 bash /opt/toddy-build/scripts/build/h07-supplemental-tools-driver.sh
 result=$?
fi
echo "$result" > "$prefix.exit"
exit "$result"
