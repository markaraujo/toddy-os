#!/bin/bash
# Prepared only: never start before final GCC critical acceptance/install.
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-gcc-install.success.json || -f /var/log/toddy/build/h07-gcc-install-recovery.success.json ]] || exit 1
for package in ncurses sed psmisc gettext bison grep glibc-test-locales bash; do
 if [[ $package == bash && -f /var/log/toddy/build/h07-bash-recovery.success.json ]]; then continue; fi
 if [[ $package == psmisc && -f /var/log/toddy/build/h07-psmisc-audit.success.json ]]; then continue; fi
 if [[ $package == ncurses && -f /var/log/toddy/build/h07-ncurses-recovery.success.json ]]; then continue; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-post-compiler-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-post-compiler-driver.exit
