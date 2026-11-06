#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h10/require_gate.py
cd "$LFS/sources"
python3 "$SOURCE_TOOL" squashfs-tools-4.7.5.tar.gz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/squashfs-tools-4.7.5/squashfs-tools
test ! -e /sources/stage/squashfs-tools
options=(GZIP_SUPPORT=1 XZ_SUPPORT=1 ZSTD_SUPPORT=1 LZO_SUPPORT=0 LZ4_SUPPORT=0 LZMA_SUPPORT=0 LZMA_XZ_SUPPORT=0 XATTR_SUPPORT=1 XATTR_OS_SUPPORT=1 COMP_DEFAULT=xz)
make "${options[@]}"
make "${options[@]}" INSTALL_DIR=/sources/stage/squashfs-tools/usr/bin \
 INSTALL_MANPAGES_DIR=/sources/stage/squashfs-tools/usr/share/man/man1 USE_PREBUILT_MANPAGES=y install
install -Dm644 ../COPYING /sources/stage/squashfs-tools/usr/share/doc/squashfs-tools/copyright
cp -a ../Documentation /sources/stage/squashfs-tools/usr/share/doc/squashfs-tools/
cat > /sources/stage/squashfs-tools/usr/share/doc/squashfs-tools/profile.txt <<'PROFILE'
Compiled compressors: gzip, xz, zstd. Default: xz. Extended attributes enabled.
The upstream prebuilt manual describes additional optional compressors;
use the installed tools' help for this build's supported options.
POSIX ACLs need the separate physical numeric sidecar (ADR-0048).
Userspace roundtrip acceptance does not establish native-kernel live boot.
PROFILE
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py squashfs-tools 4.7.5-1 \
 "$LFS/sources/stage/squashfs-tools" --depends 'glibc, zlib, xz, zstd' \
 --source squashfs-tools-4.7.5.tar.gz --recipe /opt/toddy-build/scripts/build/h10/squashfs-tools.sh --install
