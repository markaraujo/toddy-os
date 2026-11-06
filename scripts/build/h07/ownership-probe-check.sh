#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ ! -e /var/cache/toddy/packages/toddy-ownership-probe_0.1_all.deb ]]
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' man-pages) == 'install ok installed' ]]
grep 'Native package ownership conflict before install:' /var/log/toddy/ownership-probe.log
