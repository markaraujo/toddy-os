#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" man-db-2.13.1.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/man-db-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py man-db 2.13.1-1 \
 "$LFS/sources/stage/man-db" --depends 'glibc (>= 2.44-1), gdbm, libpipeline, zlib, groff, less' --source man-db-2.13.1.tar.xz --conffile /etc/man_db.conf \
 --recipe /opt/toddy-build/scripts/build/h07/man-db.sh --install
