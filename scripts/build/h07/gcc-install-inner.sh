#!/bin/bash
# Frozen LFS 13.1-systemd 8.32, stage only after accepted complete tests.
set -euo pipefail
cd /sources/gcc-16.2.0/build
stage=/sources/stage/gcc
test ! -e "$stage"
make DESTDIR="$stage" install
chown -hR root:root "$stage"
ln -sfv gcc "$stage/usr/bin/cc"
ln -svr "$stage/usr/bin/cpp" "$stage/usr/lib/cpp"
ln -sv gcc.1 "$stage/usr/share/man/man1/cc.1"
mkdir -p "$stage/usr/lib/bfd-plugins"
mapfile -t plugins < <(find "$stage/usr/libexec/gcc" -name liblto_plugin.so -type f)
[[ ${#plugins[@]} == 1 ]]
ln -sfvr "${plugins[0]}" "$stage/usr/lib/bfd-plugins/"
mkdir -p "$stage/usr/share/gdb/auto-load/usr/lib"
mv -v "$stage"/usr/lib/*gdb.py "$stage/usr/share/gdb/auto-load/usr/lib/"
mkdir -p "$stage/usr/share/doc/gcc"
cat ../COPYING ../COPYING.LIB ../COPYING3 ../COPYING3.LIB ../COPYING.RUNTIME > "$stage/usr/share/doc/gcc/copyright"
