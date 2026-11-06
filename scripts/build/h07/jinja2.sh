#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" jinja2-3.1.6.tar.gz
chroot_run < /opt/toddy-build/scripts/build/h07/jinja2-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py jinja2 3.1.6-1 \
 "$LFS/sources/stage/jinja2" --depends 'python, markupsafe' --source jinja2-3.1.6.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/jinja2.sh --install
