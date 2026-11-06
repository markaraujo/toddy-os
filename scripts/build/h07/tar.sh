#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" tar-1.35.tar.xz
python3 "$SOURCE_TOOL" --verify-only tar-1.35-acl_fix-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/tar-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py tar 1.35-1 \
 "$LFS/sources/stage/tar" --depends 'glibc (>= 2.44-1), acl, attr' --source tar-1.35.tar.xz --source tar-1.35-acl_fix-1.patch \
 --recipe /opt/toddy-build/scripts/build/h07/tar.sh --install
