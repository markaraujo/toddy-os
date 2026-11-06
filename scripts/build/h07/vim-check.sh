#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' vim) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'old\n' > /tmp/toddy-vim.txt
vim -Nu NONE -n -es -c '%s/old/VIM_NATIVE_OK/' -c wq /tmp/toddy-vim.txt
grep -Fx VIM_NATIVE_OK /tmp/toddy-vim.txt
rm /tmp/toddy-vim.txt
test -L /usr/bin/vi
INNER
