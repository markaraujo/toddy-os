#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
# Never treat raw make exit alone as critical acceptance.
python3 /opt/toddy-build/scripts/build/h07/evaluate-gcc.py
# Explicit recovery from the rejected zero-change missing-notice attempt.
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-gcc-install.failed.json').read_text())
assert r['changed_paths']==0 and r['recipe_exit']!=0
CHECK
chroot_run <<'NOTICE'
set -euo pipefail
stage=/sources/stage/gcc
test -d "$stage/usr/bin"
test ! -e /sources/stage/gcc-runtime
mkdir -p "$stage/usr/share/doc/gcc"
cd /sources/gcc-16.2.0
cat COPYING COPYING.LIB COPYING3 COPYING3.LIB COPYING.RUNTIME > "$stage/usr/share/doc/gcc/copyright"
NOTICE
python3 /opt/toddy-build/scripts/build/h07/split-gcc-runtime.py
python3 /opt/toddy-build/scripts/build/stage_package.py gcc-runtime 16.2.0-1 \
 "$LFS/sources/stage/gcc-runtime" --depends 'glibc (>= 2.44-1)' \
 --source gcc-16.2.0.tar.xz --recipe /opt/toddy-build/scripts/build/h07/gcc-install-resume.sh --install
python3 /opt/toddy-build/scripts/build/stage_package.py gcc 16.2.0-1 \
 "$LFS/sources/stage/gcc" --depends 'gcc-runtime (= 16.2.0-1), glibc (>= 2.44-1), gmp, mpfr, mpc, zlib, zstd' \
 --source gcc-16.2.0.tar.xz --recipe /opt/toddy-build/scripts/build/h07/gcc-install-resume.sh --install
chroot_run <<'INNER'
set -euo pipefail
ldconfig
INNER
