#!/bin/bash
# Verify actual staged production library before guarded package installation.
source /opt/toddy-build/scripts/build/h06/common.sh
chroot /mnt/lfs /usr/bin/env -i HOME=/root TERM=dumb LC_ALL=C \
 PATH=/sources/stage/berkeley-db/usr/bin:/usr/bin:/usr/sbin \
 CPATH=/sources/stage/berkeley-db/usr/include \
 LIBRARY_PATH=/sources/stage/berkeley-db/usr/lib \
 LD_LIBRARY_PATH=/sources/stage/berkeley-db/usr/lib \
 /usr/bin/bash --noprofile --norc -s \
 < /opt/toddy-build/scripts/build/h07/berkeley-db-check-inner.sh
