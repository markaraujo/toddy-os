#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" tcsh-6.24.16.tar.gz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/tcsh-6.24.16
test ! -e /sources/stage/tcsh
mkdir -p /sources/evidence/h07-tcsh
./configure --prefix=/usr
make
chown -R tester:tester .
su tester -c 'make check' 2>&1 | tee /sources/evidence/h07-tcsh/check.log
make DESTDIR=/sources/stage/tcsh install install.man
ln -s tcsh /sources/stage/tcsh/usr/bin/csh
ln -s tcsh.1 /sources/stage/tcsh/usr/share/man/man1/csh.1
install -Dm644 Copyright /sources/stage/tcsh/usr/share/doc/tcsh/copyright
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py tcsh 6.24.16-1 \
 "$LFS/sources/stage/tcsh" --depends 'glibc, ncurses, libxcrypt' --source tcsh-6.24.16.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/tcsh.sh --install
