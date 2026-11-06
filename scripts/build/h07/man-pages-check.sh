#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
test -f "$LFS/usr/share/doc/man-pages/LICENSES/MIT.txt"
test -f "$LFS/usr/share/doc/man-pages/copyright"
find "$LFS/usr/share/man" -name 'open.2*' | grep .
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' man-pages) == 'install ok installed' ]]
dpkg-query --admindir="$LFS/var/lib/dpkg" -L man-pages | grep '/usr/share/man/' | wc -l
