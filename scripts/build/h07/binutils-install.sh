#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
# Reclassify original reports; no installation before critical acceptance.
python3 /opt/toddy-build/scripts/build/h07/evaluate-binutils.py
chroot_run < /opt/toddy-build/scripts/build/h07/binutils-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py binutils 2.47-1 \
 "$LFS/sources/stage/binutils" --depends 'glibc (>= 2.44-1), zlib, zstd' \
 --source binutils-2.47.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/binutils-install.sh --install
# Keep the tested tree until the final native compiler/linker audit.
