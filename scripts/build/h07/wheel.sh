#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" wheel-0.48.0.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/wheel-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py wheel 0.48.0-1 \
 "$LFS/sources/stage/wheel" --depends 'python, flit-core, packaging' --source wheel-0.48.0.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/wheel.sh --install
