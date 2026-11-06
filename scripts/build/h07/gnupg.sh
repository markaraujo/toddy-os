#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" gnupg-2.5.24.tar.bz2
chroot_run < /opt/toddy-build/scripts/build/h07/gnupg-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gnupg 2.5.24-1 \
 "$LFS/sources/stage/gnupg" --depends 'glibc (>= 2.44-1), libgpg-error, libgcrypt, libassuan, libksba, npth, zlib, bzip2, readline' --source gnupg-2.5.24.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/gnupg.sh --install
