#!/bin/bash
# Resume the remaining base only after the existing Python recovery terminates.
set -uo pipefail
prefix=/var/log/toddy/h07-python-to-native-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
python_pid=$(cat /var/log/toddy/h07-python-recovery.pid)
[[ $python_pid =~ ^[0-9]+$ ]] || exit 1
if [[ -r /proc/$python_pid/cmdline ]]; then
 grep -aq 'h07-python-recovery' "/proc/$python_pid/cmdline" || exit 1
 tail --pid="$python_pid" --sleep-interval=2 -f /dev/null
fi
if [[ ! -f /var/log/toddy/build/h07-python-recovery.success.json ]]; then
 echo 'Python recovery not accepted; no later recipe started.' >&2
 echo 1 > "$prefix.exit"
 exit 1
fi
bash /opt/toddy-build/scripts/build/h07-native-tools-driver.sh
result=$?
if [[ $result == 0 ]]; then
 bash /opt/toddy-build/scripts/build/h07-system-utilities-driver.sh
 result=$?
fi
echo "$result" > "$prefix.exit"
exit "$result"
