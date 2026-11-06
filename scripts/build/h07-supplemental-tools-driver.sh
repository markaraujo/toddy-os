#!/bin/bash
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-e2fsprogs.success.json || -f /var/log/toddy/build/h07-e2fsprogs-recovery.success.json ]] || exit 1
echo $$ > /var/log/toddy/h07-supplemental-tools-driver.pid
rm -f /var/log/toddy/h07-supplemental-tools-driver.exit
for package in ca-certificates nghttp2 curl libuv libarchive cmake libmd time xxhash googletest libgpg-error libgcrypt libassuan libksba npth gnupg vim-glvs-inputs vim; do
 if [[ $package == xxhash && -f /var/log/toddy/build/h07-xxhash-recovery.success.json ]]; then continue; fi
 if [[ $package == libuv && -f /var/log/toddy/build/h07-libuv-recovery.success.json ]]; then continue; fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue; fi
 if [[ $package == vim && ! -f /var/log/toddy/build/h07-vim-glvs-inputs.success.json ]]; then
  echo 'Vim full downloader suite requires frozen/verified GLVS inputs before execution' >&2
  echo 1 > /var/log/toddy/h07-supplemental-tools-driver.exit
  exit 1
 fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > /var/log/toddy/h07-supplemental-tools-driver.exit; exit "$result"; fi
done
echo 0 > /var/log/toddy/h07-supplemental-tools-driver.exit
