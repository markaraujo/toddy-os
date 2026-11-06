#!/bin/bash
# LFS 13.1-systemd 8.5 installation adapted to staged native ownership.
set -euo pipefail
cd /sources/glibc-2.44/build
stage=/sources/stage/glibc
test ! -e "$stage"
mkdir -p "$stage/etc"
touch "$stage/etc/ld.so.conf"
# The book explicitly disables this obsolete installation-only sanity check;
# the complete critical make check suite has already been evaluated separately.
sed '/test-installation/s@$(PERL)@echo not running@' -i ../Makefile
make DESTDIR="$stage" install
sed '/RTLDLIST=/s@/usr@@g' -i "$stage/usr/bin/ldd"
# Runtime cache is derived after installation, not distributed as a stale cache.
rm -f "$stage/etc/ld.so.cache"
cat > "$stage/etc/nsswitch.conf" <<'CONFIG'
# Begin /etc/nsswitch.conf
passwd: files systemd
group: files systemd
shadow: files systemd
hosts: mymachines resolve [!UNAVAIL=return] files myhostname dns
networks: files
protocols: files
services: files
ethers: files
rpc: files
# End /etc/nsswitch.conf
CONFIG
cat > "$stage/etc/ld.so.conf" <<'CONFIG'
# Begin /etc/ld.so.conf
/usr/local/lib
/opt/lib
include /etc/ld.so.conf.d/*.conf
CONFIG
mkdir -p "$stage/etc/ld.so.conf.d" "$stage/usr/share/doc/glibc"
cp ../COPYING* ../LICENSES "$stage/usr/share/doc/glibc/"
cat ../LICENSES ../COPYING* > "$stage/usr/share/doc/glibc/copyright"
