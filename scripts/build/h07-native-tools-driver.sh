#!/bin/bash
# Continue frozen chapter 8 order after the final Bash acceptance.
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-bash.success.json || -f /var/log/toddy/build/h07-bash-recovery.success.json ]] || exit 1
echo $$ > /var/log/toddy/h07-native-tools-driver.pid
rm -f /var/log/toddy/h07-native-tools-driver.exit
for package in libtool gdbm gperf expat inetutils less perl autoconf automake openssl libelf libffi sqlite mpdecimal python flit-core packaging wheel setuptools meson; do
 if [[ $package == gperf && -f /var/log/toddy/build/h07-gperf-audit.success.json ]]; then continue; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-native-tools-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-native-tools-driver.exit
