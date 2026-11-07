#!/bin/bash
# Mount a preserved source read-only, with separately owned writable build output.
# This helper does not authorize installation or accept any test result.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
[[ $(id -u) == 0 && $# -ge 3 ]]
source_tree=$1
work=$2
shift 2
[[ $source_tree == /mnt/lfs/sources/recovery/db-standard-*/source || $source_tree == /mnt/lfs/sources/recovery/db-native-*/db-5.3.28 ]]
[[ $work == /mnt/lfs/sources/recovery/db-production-* ]]
[[ $(realpath -e "$source_tree") == "$source_tree" && $(realpath -e "$work") == "$work" ]]
[[ $(stat -c '%u:%a' "$work") == 0:700 ]]
for path in "$source_tree" "$source_tree/build-production" "$work/build-production"; do
 [[ -d $path && ! -L $path ]]
done
[[ $(realpath -e "$work/build-production") == "$work/build-production" ]]
exec 3<&0
exec unshare --mount /bin/bash -s -- "$source_tree" "$work" "$@" <<'VIEW'
set -euo pipefail
source_tree=$1
work=$2
shift 2
mount --make-rprivate /
mount --bind "$source_tree" /mnt/lfs/sources/db-5.3.28
mount -o remount,bind,ro /mnt/lfs/sources/db-5.3.28
mount --bind "$work/build-production" /mnt/lfs/sources/db-5.3.28/build-production
python3 - "$source_tree" "$work" <<'PY'
import os,sys
from pathlib import Path
source,work=map(Path,sys.argv[1:])
visible=Path('/mnt/lfs/sources/db-5.3.28')
assert os.path.samefile(source,visible)
assert os.path.samefile(work/'build-production',visible/'build-production')
assert os.statvfs(visible).f_flag & os.ST_RDONLY
assert not os.statvfs(visible/'build-production').f_flag & os.ST_RDONLY
PY
exec "$@" <&3 3<&-
VIEW
