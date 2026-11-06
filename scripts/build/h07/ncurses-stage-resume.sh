#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" --verify-only ncurses-6.6.tar.gz
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-ncurses.failed.json').read_text())
assert r['changed_paths']==0 and r['recipe_exit']!=0
CHECK
chroot_run <<'DOCS'
set -euo pipefail
cd /sources/ncurses-6.6
test -d /sources/stage/ncurses/usr/lib
mkdir -p /sources/stage/ncurses/usr/share/doc
cp -v -R doc -T /sources/stage/ncurses/usr/share/doc/ncurses-6.6
mkdir -p /sources/stage/ncurses/usr/share/doc/ncurses
cp COPYING /sources/stage/ncurses/usr/share/doc/ncurses/copyright
DOCS
python3 /opt/toddy-build/scripts/build/stage_package.py ncurses 6.6-1 \
 "$LFS/sources/stage/ncurses" --depends 'glibc (>= 2.44-1), gcc-runtime' --source ncurses-6.6.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/ncurses-stage-resume.sh --install
