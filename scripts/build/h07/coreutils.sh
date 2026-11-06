#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" coreutils-9.11.tar.xz
python3 "$SOURCE_TOOL" --verify-only coreutils-9.11-i18n-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/coreutils-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py coreutils 9.11-1 \
 "$LFS/sources/stage/coreutils" --depends 'glibc (>= 2.44-1), gmp, acl, attr, libcap' --source coreutils-9.11.tar.xz --source coreutils-9.11-i18n-1.patch \
 --recipe /opt/toddy-build/scripts/build/h07/coreutils.sh --install
