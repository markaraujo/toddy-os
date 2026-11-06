#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" mpdecimal-4.0.1.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/mpdecimal-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py mpdecimal 4.0.1-1 \
 "$LFS/sources/stage/mpdecimal" --depends 'glibc (>= 2.44-1), gcc-runtime' --source mpdecimal-4.0.1.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/mpdecimal.sh --install
