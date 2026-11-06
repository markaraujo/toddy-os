#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-glibc-install.success.json ]] || exit 1
mkdir "$LFS/sources/tzdata-2026c"
cd "$LFS/sources/tzdata-2026c"
python3 "$SOURCE_TOOL" tzdata2026c.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/tzdata-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py tzdata 2026c-1 \
    "$LFS/sources/stage/tzdata" --architecture all --source tzdata2026c.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/tzdata.sh --install
rm -rf "$LFS/sources/tzdata-2026c"
