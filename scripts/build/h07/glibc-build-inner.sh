#!/bin/bash
# LFS 13.1-systemd 8.5, explicit stable security overlay in ADR-0009.
set -euo pipefail
cd /sources/glibc-2.44
patch -Np1 -i ../glibc-fhs-1.patch
patch -Np1 -i ../glibc-2.44-upstream_fixes-3.patch
mkdir build
cd build
../configure --prefix=/usr --disable-werror --disable-nscd \
    libc_cv_slibdir=/usr/lib --enable-stack-protector=strong --enable-kernel=5.10
make
mkdir -p /sources/evidence/h07-glibc
# Preserve nonzero status for strict classification; never infer a suite pass.
set +e
make check > /sources/evidence/h07-glibc/make-check.log 2>&1
suite_exit=$?
set -e
echo "$suite_exit" > /sources/evidence/h07-glibc/make-check.exit
test -s tests.sum
cp tests.sum /sources/evidence/h07-glibc/tests-original.sum
find . -type f \( -name '*.out' -o -name '*.test-result' -o -name 'tests.sum' \) -print0 \
    | tar --null -T - -cf /sources/evidence/h07-glibc/raw-test-results.tar
cp config.log /sources/evidence/h07-glibc/config.log
