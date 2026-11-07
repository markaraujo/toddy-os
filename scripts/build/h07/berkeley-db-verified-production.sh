#!/bin/bash
# Only a complete, independently verified native suite may enter production.
source /opt/toddy-build/scripts/build/h06/common.sh
fixture=$(python3 -B /opt/toddy-build/scripts/build/db_standard_handoff.py consume)
[[ $fixture == /mnt/lfs/sources/recovery/db-standard-* ]]
[[ $(realpath -e -- "$fixture") == "$fixture" ]]
[[ ! -e $LFS/sources/stage/berkeley-db ]]
# Preserve the tested source/custody tree; only a separate output directory is writable.
work=$(mktemp -d "$LFS/sources/recovery/db-production-XXXXXXXX")
mkdir -m 700 "$work/build-production"
printf '%s\n' "$fixture" > "$work/tested-fixture"
printf 'Production workspace: %s\n' "$work"
exec bash /opt/toddy-build/scripts/build/h07/berkeley-db-production-view.sh \
 "$fixture/source" "$work" /bin/bash -s -- "$fixture" "$0" <<'NAMESPACE'
set -euo pipefail
fixture=$1
recipe=$2
source /opt/toddy-build/scripts/build/h06/common.sh
evidence=$LFS/sources/evidence/h07-berkeley-db/isolated-standard
[[ ! -e $evidence && ! -L $evidence ]]
mkdir -m 700 "$evidence"
cp "$fixture"/result-evidence/{ALL.OUT,standard.log,cutest.log,isolation-standard.json} "$evidence/"
cp "$fixture"/{inputs.json,result.json} "$evidence/"
cp /var/log/toddy/build/h07-berkeley-db.standard-candidate.json "$evidence/candidate.json"
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-production-inner.sh
bash /opt/toddy-build/scripts/build/h07/berkeley-db-package.sh "$recipe"
NAMESPACE
