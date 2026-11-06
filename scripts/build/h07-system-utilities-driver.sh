#!/bin/bash
# Frozen chapter 8 continuation; boot-sector installation belongs to H09.
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-meson.success.json ]] || exit 1
echo $$ > /var/log/toddy/h07-system-utilities-driver.pid
rm -f /var/log/toddy/h07-system-utilities-driver.exit
for package in kmod coreutils diffutils findutils groff grub gzip iproute2 kbd libpipeline make patch tar texinfo; do
 if [[ $package == tar && -f /var/log/toddy/build/h07-tar-recovery.success.json ]]; then continue; fi
 if [[ $package == kbd && -f /var/log/toddy/build/h07-kbd-recovery.success.json ]]; then continue; fi
 if [[ $package == groff && -f /var/log/toddy/build/h07-groff-recovery.success.json ]]; then continue; fi
 if [[ $package == findutils && -f /var/log/toddy/build/h07-findutils-recovery.success.json ]]; then continue; fi
 if [[ $package == coreutils && -f /var/log/toddy/build/h07-coreutils-recovery.success.json ]]; then continue; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-system-utilities-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-system-utilities-driver.exit
