#!/bin/bash
set -uo pipefail
cd /opt/toddy-build/scripts/build
[[ -f /var/log/toddy/build/h07-dpkg.success.json ]] || exit 1
prefix=/var/log/toddy/h07-perl-test-tools-driver
echo $$ > "$prefix.pid"
rm -f "$prefix.exit"
mapfile -t packages < <(python3 -c 'import json; print("\n".join(r["package"] for r in json.load(open("/opt/toddy-build/config/native-perl-test-tools.lock.json"))["components"]))')
for package in "${packages[@]}" triehash which libseccomp tcsh; do
 if [[ -f /var/log/toddy/h07-input-handoff.request ]]; then echo 75 > "$prefix.exit";exit 75;fi
 if [[ -f /var/log/toddy/build/h07-$package.success.json ]]; then continue;fi
 python3 run_step.py "h07-$package" "h07/$package.sh" "h07/$package-check.sh" --user root
 result=$?
 if [[ $result != 0 ]]; then echo "$result" > "$prefix.exit";exit "$result";fi
done
echo 0 > "$prefix.exit"
