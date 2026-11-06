#!/bin/bash
# Wait for the existing native-tools driver, then continue only on acceptance.
set -uo pipefail
prefix=/var/log/toddy/h07-native-to-utilities-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
native_pid=$(cat /var/log/toddy/h07-native-tools-driver.pid)
[[ $native_pid =~ ^[0-9]+$ ]] || exit 1
if [[ -r /proc/$native_pid/cmdline ]]; then
 grep -aq 'h07-native-tools-driver.sh' "/proc/$native_pid/cmdline" || exit 1
 tail --pid="$native_pid" --sleep-interval=2 -f /dev/null
fi
if [[ ! -f /var/log/toddy/build/h07-meson.success.json ]]; then
 echo 'Native-tools prerequisite not accepted; no utility recipe started.' >&2
 echo 1 > "$prefix.exit"
 exit 1
fi
bash /opt/toddy-build/scripts/build/h07-system-utilities-driver.sh
result=$?
echo "$result" > "$prefix.exit"
exit "$result"
