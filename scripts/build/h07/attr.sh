#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" attr-2.6.0.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/attr-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py attr 2.6.0-1 \
 "$LFS/sources/stage/attr" --depends 'glibc (>= 2.44-1)' --source attr-2.6.0.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/attr.sh --conffile /etc/xattr.conf --install
rm -rf "$LFS/sources/attr-2.6.0"
