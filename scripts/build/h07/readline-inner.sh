#!/bin/bash
# Frozen chapter 8 commands, reviewed DESTDIR adaptation; security deltas explicit.
set -euo pipefail
cd /sources/readline-8.3
test ! -e /sources/stage/readline
sed -i '/MV.*old/d' Makefile.in
sed -i '/{OLDSUFF}/c:' support/shlib-install

sed -i 's/-Wl,-rpath,[^ ]*//' support/shobj-conf

sed -e '270a\
     else\
       chars_avail = 1;'      \
    -e '288i\   result = -1;' \
    -i.orig input.c

./configure --prefix=/usr    \
            --disable-static \
            --with-curses    \
            --docdir=/usr/share/doc/readline-8.3

make SHLIB_LIBS="-lncursesw"

make DESTDIR=/sources/stage/readline install

install -v -m644 doc/*.{ps,pdf,html,dvi} /sources/stage/readline/usr/share/doc/readline-8.3
mkdir -p /sources/stage/readline/usr/share/doc/readline
cat COPYING > /sources/stage/readline/usr/share/doc/readline/copyright
