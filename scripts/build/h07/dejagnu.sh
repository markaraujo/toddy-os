#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" dejagnu-1.6.3.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/dejagnu-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py dejagnu 1.6.3-1 \
    "$LFS/sources/stage/dejagnu" --depends 'expect, tcl' --source dejagnu-1.6.3.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/dejagnu.sh --install
rm -rf "$LFS/sources/dejagnu-1.6.3"
