#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' glibc-test-locales) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
LC_ALL=ja_JP.SJIS locale charmap | grep -Fx SHIFT_JIS
LC_ALL=zh_TW.BIG5 locale charmap | grep -Fx BIG5
LC_ALL=pt_BR.UTF-8 locale charmap | grep -Fx UTF-8
INNER
