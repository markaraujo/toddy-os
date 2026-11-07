#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' berkeley-db) == 'install ok installed' ]]
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-check-inner.sh
