#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gdbm-1.26.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/gdbm-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gdbm 1.26-1 \
 "$LFS/sources/stage/gdbm" --depends 'glibc (>= 2.44-1), readline' --source gdbm-1.26.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/gdbm.sh --install
