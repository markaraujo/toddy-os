#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" libffi-3.8.0.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/libffi-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libffi 3.8.0-1 \
 "$LFS/sources/stage/libffi" --depends 'glibc (>= 2.44-1)' --source libffi-3.8.0.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/libffi.sh --install
