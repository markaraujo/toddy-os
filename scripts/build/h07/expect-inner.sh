#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: expect; staged install.
set -euo pipefail
cd /sources/expect5.45.4
test ! -e /sources/stage/expect
# pty.spawn also reads its own stdin; do not let it consume the remaining
# recipe streamed into chroot Bash. Probe input is deliberately empty.
python3 -c 'from pty import spawn; spawn(["echo", "ok"])' < /dev/null

patch -Np1 -i ../expect-5.45.4-gcc15-1.patch

./configure --prefix=/usr           \
            --with-tcl=/usr/lib     \
            --enable-shared         \
            --disable-rpath         \
            --mandir=/usr/share/man \
            --with-tclinclude=/usr/include

make

make test

make DESTDIR=/sources/stage/expect install
ln -svf expect5.45.4/libexpect5.45.4.so /sources/stage/expect/usr/lib
mkdir -p /sources/stage/expect/usr/share/doc/expect
cp license.terms /sources/stage/expect/usr/share/doc/expect/copyright
