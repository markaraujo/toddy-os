#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' iana-etc) == 'install ok installed' ]]
dpkg-query --admindir="$LFS/var/lib/dpkg" -S /etc/services /etc/protocols
grep -E '^tcp[[:space:]]+6' "$LFS/etc/protocols"
grep -E '^ssh[[:space:]]+22/tcp' "$LFS/etc/services"
test -f "$LFS/usr/share/doc/iana-etc/copyright"
