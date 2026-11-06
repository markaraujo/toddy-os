#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $# == 1 ]]
package=$1
mapfile -t fields < <(python3 - "$package" <<'PY'
import json,sys
from pathlib import Path
root=Path('/opt/toddy-build')
rows=json.loads((root/'config/native-perl-test-tools.lock.json').read_text())['components']
r=next(r for r in rows if r['package']==sys.argv[1])
for field in ('filename','source_directory','version'):print(r[field])
print(', '.join(r['depends']))
PY
)
[[ ${#fields[@]} == 4 ]]
cd "$LFS/sources"
python3 "$SOURCE_TOOL" "${fields[0]}"
# Arguments are data from the committed manifest, not evaluated shell fragments.
# The inner script is passed on stdin; no builder binaries enter the target.
chroot /mnt/lfs /usr/bin/env -i HOME=/root PATH=/usr/bin:/usr/sbin LC_ALL=en_US.UTF-8 MAKEFLAGS=-j8 \
 /bin/bash -s -- "$package" "${fields[1]}" < /opt/toddy-build/scripts/build/h07/perl-test-tool-inner.sh
python3 /opt/toddy-build/scripts/build/perl_packlists.py "$LFS/sources/stage/$package" "$package"
python3 /opt/toddy-build/scripts/build/stage_package.py "$package" "${fields[2]}-1" \
 "$LFS/sources/stage/$package" --depends "${fields[3]}" --source "${fields[0]}" \
 --recipe /opt/toddy-build/scripts/build/h07/perl-test-tool.sh --install
