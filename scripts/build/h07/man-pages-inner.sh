#!/bin/bash
# LFS 13.1-systemd 8.3; DESTDIR staging per ADR-0008.
set -euo pipefail
cd /sources/man-pages-6.18
rm -v man3/crypt*
make -R GIT=false prefix=/usr DESTDIR=/sources/stage/man-pages install
mkdir -p /sources/stage/man-pages/usr/share/doc/man-pages
cp -a AUTHORS LICENSES /sources/stage/man-pages/usr/share/doc/man-pages/
cat > /sources/stage/man-pages/usr/share/doc/man-pages/copyright <<'NOTICE'
Linux man-pages 6.18 retains individual page copyright and license notices.
See each installed manual's source header and the accompanying LICENSES and
AUTHORS files; there is no single blanket license for the collection.
Source: https://www.kernel.org/pub/linux/docs/man-pages/man-pages-6.18.tar.xz
NOTICE
