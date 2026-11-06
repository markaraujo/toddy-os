#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' zlib) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c 'import zlib; assert zlib.ZLIB_RUNTIME_VERSION == "1.3.2"; assert zlib.decompress(zlib.compress(b"native-zlib")) == b"native-zlib"; print("Packaged zlib works")'
INNER
