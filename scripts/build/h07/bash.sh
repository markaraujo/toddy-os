#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" bash-5.3.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/bash-inner.sh
python3 /opt/toddy-build/scripts/build/h07/evaluate-bash.py
chroot_run < /opt/toddy-build/scripts/build/h07/bash-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py bash 5.3-1 \
 "$LFS/sources/stage/bash" --depends 'glibc (>= 2.44-1), readline, ncurses' --source bash-5.3.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/bash.sh --install
