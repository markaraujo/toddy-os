#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" flex-2.6.4.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/flex-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py flex 2.6.4-1 \
    "$LFS/sources/stage/flex" --depends 'glibc (>= 2.44-1)' --source flex-2.6.4.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/flex.sh --install
rm -rf "$LFS/sources/flex-2.6.4"
