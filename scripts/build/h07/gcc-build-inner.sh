#!/bin/bash
# Frozen LFS 13.1-systemd 8.32; actual critical suite before installation.
set -euo pipefail
cd /sources/gcc-16.2.0
case $(uname -m) in
 x86_64) sed -e '/m64=/s/lib64/lib/' -i.orig gcc/config/i386/t-linux64 ;;
esac
mkdir build
cd build
../configure --prefix=/usr LD=ld --enable-languages=c,c++ \
 --enable-default-pie --enable-default-ssp --enable-host-pie \
 --enable-targets=all --disable-multilib --disable-bootstrap \
 --disable-fixincludes --with-system-zlib
make
ulimit -s -H unlimited
chown -R tester .
mkdir -p /sources/evidence/h07-gcc
set +e
su tester -c "PATH=$PATH make -k check" > /sources/evidence/h07-gcc/check.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /sources/evidence/h07-gcc/check.exit
# This command prints a report script; never execute its output or send mail.
../contrib/test_summary -t > /sources/evidence/h07-gcc/test-summary.txt
find . -type f \( -name '*.sum' -o -name '*.log' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-gcc/test-reports.tar.gz
cat /sources/evidence/h07-gcc/test-summary.txt
exit "$result"
