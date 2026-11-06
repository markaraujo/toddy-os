#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" pcre2-10.49.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/pcre2-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py pcre2 10.49-1 \
    "$LFS/sources/stage/pcre2" --depends 'glibc (>= 2.44-1), zlib, bzip2, readline' --source pcre2-10.49.tar.bz2 \
    --recipe /opt/toddy-build/scripts/build/h07/pcre2.sh --install
rm -rf "$LFS/sources/pcre2-10.49"
