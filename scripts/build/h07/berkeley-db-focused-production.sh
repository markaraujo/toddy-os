#!/bin/bash
# ADR-0092 recovery path: use verified completed native compilation/C tests.
source /opt/toddy-build/scripts/build/h06/common.sh
pointer=/var/log/toddy/build/h07-berkeley-db.focused-source
[[ -f $pointer && ! -L $pointer && $(stat -c '%u:%a' "$pointer") == 0:600 ]]
fixture=$(cat "$pointer")
[[ $fixture == /mnt/lfs/sources/recovery/db-native-* && $(realpath -e "$fixture") == "$fixture" ]]
[[ ! -e $LFS/sources/stage/berkeley-db ]]
evidence=$LFS/sources/evidence/h07-berkeley-db/focused-production
[[ ! -e $evidence ]]
mkdir -m700 "$evidence"
python3 -B /opt/toddy-build/scripts/build/db_native_build_result.py "$fixture" > "$evidence/native-build-verification.json"
work=$(mktemp -d "$LFS/sources/recovery/db-production-XXXXXXXX")
mkdir -m700 "$work/build-production"
printf '%s\n' "$fixture" > "$work/tested-fixture"
printf 'Focused production workspace: %s\n' "$work"
exec bash /opt/toddy-build/scripts/build/h07/berkeley-db-production-view.sh \
 "$fixture/db-5.3.28" "$work" /bin/bash -s -- "$0" <<'NAMESPACE'
set -euo pipefail
recipe=$1
source /opt/toddy-build/scripts/build/h06/common.sh
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-production-inner.sh
bash /opt/toddy-build/scripts/build/h07/berkeley-db-focused-stage-check.sh
bash /opt/toddy-build/scripts/build/h07/berkeley-db-package.sh "$recipe"
NAMESPACE
