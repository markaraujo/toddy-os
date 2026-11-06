#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
# Never treat raw make exit alone as critical acceptance.
python3 /opt/toddy-build/scripts/build/h07/evaluate-gcc.py
chroot_run < /opt/toddy-build/scripts/build/h07/gcc-install-inner.sh
python3 /opt/toddy-build/scripts/build/h07/split-gcc-runtime.py
python3 /opt/toddy-build/scripts/build/stage_package.py gcc-runtime 16.2.0-1 \
 "$LFS/sources/stage/gcc-runtime" --depends 'glibc (>= 2.44-1)' \
 --source gcc-16.2.0.tar.xz --recipe /opt/toddy-build/scripts/build/h07/gcc-install.sh --install
python3 /opt/toddy-build/scripts/build/stage_package.py gcc 16.2.0-1 \
 "$LFS/sources/stage/gcc" --depends 'gcc-runtime (= 16.2.0-1), glibc (>= 2.44-1), gmp, mpfr, mpc, zlib, zstd' \
 --source gcc-16.2.0.tar.xz --recipe /opt/toddy-build/scripts/build/h07/gcc-install.sh --install
chroot_run <<'INNER'
set -euo pipefail
ldconfig
INNER
