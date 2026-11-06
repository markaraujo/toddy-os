#!/bin/bash
set -uo pipefail
prefix=/var/log/toddy/h07-gnupg-recovery-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
cd /opt/toddy-build/scripts/build
result=0
# Independent verified download preflight can run before local CMS rebuild.
if [[ ! -f /var/log/toddy/build/h07-vim-glvs-inputs.success.json ]]; then
 python3 run_step.py h07-vim-glvs-inputs h07/vim-glvs-inputs.sh h07/vim-glvs-inputs-check.sh --user root
 result=$?
fi
if [[ $result == 0 ]]; then
 python3 run_step.py h07-gnupg-recovery h07/gnupg-resume.sh h07/gnupg-check.sh --user root
 result=$?
fi
if [[ $result == 0 ]]; then
 bash /opt/toddy-build/scripts/build/h07-supplemental-tools-driver.sh
 result=$?
fi
echo "$result" > "$prefix.exit"
exit "$result"
