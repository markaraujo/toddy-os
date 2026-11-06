#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" flit_core-4.0.2.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/flit-core-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py flit-core 4.0.2-1 \
 "$LFS/sources/stage/flit-core" --depends 'python' --source flit_core-4.0.2.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/flit-core.sh --install
