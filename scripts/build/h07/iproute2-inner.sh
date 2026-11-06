#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.67-8.73; Patch overlay is ADR-0013.
set -euo pipefail
cd /sources/iproute2-7.1.0
test ! -e /sources/stage/iproute2
mkdir -p /sources/evidence/h07-iproute2
sed -i /ARPD/d Makefile
rm -f man/man8/arpd.8
make NETNS_RUN_DIR=/run/netns
# LFS 13.1 8.67: no working upstream suite; native network checks remain.
make DESTDIR=/sources/stage/iproute2 SBINDIR=/usr/sbin install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-iproute2/test-reports.tar.gz
mkdir -p /sources/stage/iproute2/usr/share/doc/iproute2
cp COPYING /sources/stage/iproute2/usr/share/doc/iproute2/copyright
