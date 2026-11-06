#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" packaging-26.3.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/packaging-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py packaging 26.3-1 \
 "$LFS/sources/stage/packaging" --depends 'python, flit-core' --source packaging-26.3.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/packaging.sh --install
