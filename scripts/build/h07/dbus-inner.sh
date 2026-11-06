#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; guarded disposable target only.
set -euo pipefail
cd /sources/dbus-1.16.2
test ! -e /sources/stage/dbus
mkdir -p /sources/evidence/h07-dbus
mkdir build
cd build
meson setup --prefix=/usr --buildtype=release --wrap-mode=nofallback ..
ninja -j8
ninja test 2>&1 | tee /sources/evidence/h07-dbus/check.log
DESTDIR=/sources/stage/dbus ninja install
mkdir -p /sources/stage/dbus/var/lib/dbus
ln -s /etc/machine-id /sources/stage/dbus/var/lib/dbus/machine-id
cp -a meson-logs /sources/evidence/h07-dbus/
cd ..
mkdir -p /sources/stage/dbus/usr/share/doc/dbus
cp -a LICENSES /sources/stage/dbus/usr/share/doc/dbus/

mkdir -p /sources/stage/dbus/usr/share/doc/dbus
cat COPYING > /sources/stage/dbus/usr/share/doc/dbus/copyright
