#!/bin/bash
set -euo pipefail
cd /sources/tcl8.6.18
test ! -e /sources/stage/tcl
SRCDIR=$(pwd)
cd unix
./configure --prefix=/usr           \
            --mandir=/usr/share/man \
            --disable-rpath

make

sed -e "s|$SRCDIR/unix|/usr/lib|" \
    -e "s|$SRCDIR|/usr/include|"  \
    -i tclConfig.sh

sed -e "s|$SRCDIR/unix/pkgs/tdbc1.1.13|/usr/lib/tdbc1.1.13|" \
    -e "s|$SRCDIR/pkgs/tdbc1.1.13/generic|/usr/include|"     \
    -e "s|$SRCDIR/pkgs/tdbc1.1.13/library|/usr/lib/tcl8.6|"  \
    -e "s|$SRCDIR/pkgs/tdbc1.1.13|/usr/include|"             \
    -i pkgs/tdbc1.1.13/tdbcConfig.sh

sed -e "s|$SRCDIR/unix/pkgs/itcl4.3.7|/usr/lib/itcl4.3.7|" \
    -e "s|$SRCDIR/pkgs/itcl4.3.7/generic|/usr/include|"    \
    -e "s|$SRCDIR/pkgs/itcl4.3.7|/usr/include|"            \
    -i pkgs/itcl4.3.7/itclConfig.sh

unset SRCDIR

LC_ALL=C.UTF-8 make test

make INSTALL_ROOT=/sources/stage/tcl install
chmod 644 /sources/stage/tcl/usr/lib/libtclstub8.6.a

chmod -v u+w /sources/stage/tcl/usr/lib/libtcl8.6.so

make INSTALL_ROOT=/sources/stage/tcl install-private-headers

ln -sfv tclsh8.6 /sources/stage/tcl/usr/bin/tclsh

mv -v /sources/stage/tcl/usr/share/man/man3/{Thread,Tcl_Thread}.3

cd ..
tar -xf ../tcl8.6.18-html.tar.gz --strip-components=1
mkdir -v -p /sources/stage/tcl/usr/share/doc/tcl-8.6.18
cp -v -r  ./html/* /sources/stage/tcl/usr/share/doc/tcl-8.6.18
mkdir -p /sources/stage/tcl/usr/share/doc/tcl
cp license.terms /sources/stage/tcl/usr/share/doc/tcl/copyright
