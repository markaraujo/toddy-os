#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' meson) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 -c 'import mesonbuild; import importlib.metadata as m; assert m.version("meson")=="1.12.0"; print("meson native import OK")'
mkdir /tmp/toddy-meson
cd /tmp/toddy-meson
printf "project('toddy-check', 'c')\nexecutable('native', 'main.c')\n" > meson.build
printf 'int main(void) {return 0;}\n' > main.c
meson setup build
ninja -C build
./build/native
cd /
rm -rf /tmp/toddy-meson
INNER
