#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" perl-5.44.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/perl-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py perl 5.44.0-1 \
 "$LFS/sources/stage/perl" --depends 'glibc (>= 2.44-1), gdbm, zlib, bzip2' --source perl-5.44.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/perl.sh --install
