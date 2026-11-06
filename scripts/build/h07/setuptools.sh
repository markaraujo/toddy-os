#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" setuptools-84.0.0.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/setuptools-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py setuptools 84.0.0-1 \
 "$LFS/sources/stage/setuptools" --depends 'python' --source setuptools-84.0.0.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/setuptools.sh --install
