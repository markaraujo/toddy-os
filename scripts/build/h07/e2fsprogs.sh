#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" e2fsprogs-1.47.4.tar.gz
install -m644 /opt/toddy-build/scripts/build/h07/evaluate-e2fs.py "$LFS/sources/toddy-evaluate-e2fs.py"
chroot_run < /opt/toddy-build/scripts/build/h07/e2fsprogs-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py e2fsprogs 1.47.4-1 \
 "$LFS/sources/stage/e2fsprogs" --depends 'glibc (>= 2.44-1), util-linux' --source e2fsprogs-1.47.4.tar.gz --conffile /etc/mke2fs.conf --conffile /etc/e2scrub.conf \
 --recipe /opt/toddy-build/scripts/build/h07/e2fsprogs.sh --install
