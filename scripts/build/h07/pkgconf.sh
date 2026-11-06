#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" pkgconf-3.0.5.tar.xz
python3 "$SOURCE_TOOL" --verify-only meson-1.12.0.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/pkgconf-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py pkgconf 3.0.5-1 \
    "$LFS/sources/stage/pkgconf" --depends 'glibc (>= 2.44-1)' --source pkgconf-3.0.5.tar.xz --source meson-1.12.0.tar.gz \
    --recipe /opt/toddy-build/scripts/build/h07/pkgconf.sh --install
rm -rf "$LFS/sources/pkgconf-3.0.5"
