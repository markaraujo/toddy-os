#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.60-8.66; build only in guarded target.
set -euo pipefail
cd /sources/findutils-4.11.0
test ! -e /sources/stage/findutils
mkdir -p /sources/evidence/h07-findutils
# ADR-0020: the shipped Gnulib regex fixes measured glibc bug 20381.
gl_cv_func_re_compile_pattern_working=no ./configure --prefix=/usr --localstatedir=/var/lib/locate
make
chown -R tester .
su tester -c "PATH=$PATH make check -k" 2>&1 | tee /sources/evidence/h07-findutils/check.log
grep -Fx 'PASS: test-regex-el' /sources/evidence/h07-findutils/check.log
make DESTDIR=/sources/stage/findutils install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-findutils/test-reports.tar.gz
mkdir -p /sources/stage/findutils/usr/share/doc/findutils
cat COPYING > /sources/stage/findutils/usr/share/doc/findutils/copyright
