#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $# == 1 ]]
python3 /opt/toddy-build/scripts/build/stage_package.py berkeley-db 5.3.28+dfsg2-12.1 \
 "$LFS/sources/stage/berkeley-db" --depends 'glibc (>= 2.44-1)' \
 --source db5.3_5.3.28+dfsg2.orig.tar.xz --source db5.3_5.3.28+dfsg2-12.debian.tar.xz \
 --source db-5.3.28-test142-environment-1.patch --recipe "$1" --install
