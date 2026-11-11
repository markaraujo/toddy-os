#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PYTHONDONTWRITEBYTECODE=1
if [[ ${1:-} != guarded ]]; then
 exec python3 /src/toddy-capacity-guard.py bash /src/toddy-build.sh guarded
fi
ulimit -c 0
python3 - <<'PY'
from pathlib import Path
import shutil
assert shutil.disk_usage('/build').free>=1024**3
shutil.copytree('/src','/build/source',symlinks=True)
PY
cd /build/source
./configure --prefix=/usr --with-gitconfig=/etc/gitconfig \
 --with-python=python3 --with-libpcre2 > /build/configure.log 2>&1
# Supported upstream C-only profile; omit optional Tk GUI from the CLI base.
make -j4 NO_RUST=YesPlease NO_TCLTK=YesPlease > /build/original-build.log 2>&1
printf '0\n' > /build/compile.exit
GIT_UNZIP=nonexist make -j4 NO_RUST=YesPlease NO_TCLTK=YesPlease test -k > /build/original-tests.log 2>&1
printf '0\n' > /build/original-tests.exit
make NO_RUST=YesPlease NO_TCLTK=YesPlease perllibdir=/usr/lib/perl5/5.44/site_perl \
 DESTDIR=/stage install > /build/original-stage.log 2>&1
printf '0\n' > /build/stage.exit
python3 /src/toddy-build-result.py
