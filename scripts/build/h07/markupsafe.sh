#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" markupsafe-3.0.3.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/markupsafe-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py markupsafe 3.0.3-1 \
 "$LFS/sources/stage/markupsafe" --depends 'python' --source markupsafe-3.0.3.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/markupsafe.sh --install
