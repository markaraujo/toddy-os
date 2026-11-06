#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' flex) == 'install ok installed' ]]
check_native /usr/bin/flex 2.6.4
