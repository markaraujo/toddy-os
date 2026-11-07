#!/bin/bash
set -euo pipefail
cd /opt/toddy-build/scripts/build
prefix=/var/log/toddy/h11-python-qa-driver
[[ ! -e $prefix.pid && ! -e $prefix.exit ]] || {
    echo 'Inspect and preserve the previous QA driver before retry' >&2
    exit 1
}
echo $$ > "$prefix.pid"
trap 'result=$?; echo "$result" > "$prefix.exit"' EXIT
python3 run_step.py h11-python-qa h11/python-qa.sh h11/python-qa-check.sh --user root
