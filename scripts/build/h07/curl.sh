#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" curl-8.23.0.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/curl-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py curl 8.23.0-1 \
 "$LFS/sources/stage/curl" --depends 'glibc (>= 2.44-1), openssl, ca-certificates, zlib, zstd, nghttp2' --source curl-8.23.0.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/curl.sh --install
