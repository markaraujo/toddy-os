#!/bin/bash
# Frozen chapter 8 commands, reviewed DESTDIR adaptation; security deltas explicit.
set -euo pipefail
cd /sources/pcre2-10.49
test ! -e /sources/stage/pcre2
./configure --prefix=/usr                       \
            --docdir=/usr/share/doc/pcre2-10.49 \
            --enable-unicode                    \
            --enable-jit                        \
            --enable-pcre2-16                   \
            --enable-pcre2-32                   \
            --enable-pcre2grep-libz             \
            --enable-pcre2grep-libbz2           \
            --enable-pcre2test-libreadline      \
            --disable-static

make

make check

make DESTDIR=/sources/stage/pcre2 install
mkdir -p /sources/stage/pcre2/usr/share/doc/pcre2
cat COPYING > /sources/stage/pcre2/usr/share/doc/pcre2/copyright
