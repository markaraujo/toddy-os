#!/bin/bash
# Independent final-base ownership work; APT/BDB acceptance stays mandatory.
set -uo pipefail
cd /opt/toddy-build/scripts/build
prefix=/var/log/toddy/h07-base-ownership-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
trap 'result=$?; echo "$result" > "$prefix.exit"' EXIT
for prerequisite in dpkg which libseccomp tcsh; do
 [[ -f /var/log/toddy/build/h07-$prerequisite.success.json ]] || { echo "Missing accepted $prerequisite";exit 1; }
done
[[ -f /var/log/toddy/build/h07-coreutils.success.json || -f /var/log/toddy/build/h07-coreutils-recovery.success.json ]] || { echo 'Missing accepted final Coreutils';exit 1; }
for package in acl-final-retest linux-api-headers filesystem-layout lfs-build-support; do
 if [[ -f /var/log/toddy/h07-input-handoff.request ]]; then echo 75 > "$prefix.exit";exit 75;fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue;fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > "$prefix.exit";exit "$result";fi
done
echo 0 > "$prefix.exit"
