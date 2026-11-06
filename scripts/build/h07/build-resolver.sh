#!/bin/bash
# Temporary build-only DNS, matching this disposable QEMU guest's uplink.
source /opt/toddy-build/scripts/build/h06/common.sh
test ! -e "$LFS/etc/resolv.conf"
test ! -L "$LFS/etc/resolv.conf"
grep -Fx 'nameserver 10.0.2.3' /run/systemd/resolve/resolv.conf
cat > "$LFS/etc/resolv.conf" <<'RESOLVER'
# Temporary Toddy build chroot resolver; H08 must replace with runtime DNS.
nameserver 10.0.2.3
RESOLVER
chmod 644 "$LFS/etc/resolv.conf"
