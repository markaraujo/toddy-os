#!/bin/bash
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-texinfo.success.json ]] || exit 1
echo $$ > /var/log/toddy/h07-final-services-driver.pid
rm -f /var/log/toddy/h07-final-services-driver.exit
for package in markupsafe jinja2 systemd dbus man-db procps-ng util-linux e2fsprogs; do
 if [[ $package == e2fsprogs && -f /var/log/toddy/build/h07-e2fsprogs-recovery.success.json ]]; then continue; fi
 if [[ $package == systemd && -f /var/log/toddy/build/h07-systemd-recovery.success.json ]]; then continue; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-final-services-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-final-services-driver.exit
