#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" openssl-4.0.3.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/openssl-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py openssl 4.0.3-1 \
 "$LFS/sources/stage/openssl" --depends 'glibc (>= 2.44-1), zlib, perl' --source openssl-4.0.3.tar.gz --conffile /etc/ssl/openssl.cnf \
 --recipe /opt/toddy-build/scripts/build/h07/openssl.sh --install
