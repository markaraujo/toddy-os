#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" make-4.4.1.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/make-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py make 4.4.1-1 \
 "$LFS/sources/stage/make" --depends 'glibc (>= 2.44-1)' --source make-4.4.1.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/make.sh --install
