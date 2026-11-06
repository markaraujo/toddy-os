#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' libarchive) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
bsdtar --version | grep -F '3.8.11'
fixture=$(mktemp -d /tmp/toddy-archive.XXXXXX)
trap 'rm -rf "$fixture"' EXIT
mkdir "$fixture/in" "$fixture/out"
printf 'native archive roundtrip\n' > "$fixture/in/data"
bsdtar -cf "$fixture/probe.tar.zst" --zstd -C "$fixture/in" data
bsdtar -xf "$fixture/probe.tar.zst" -C "$fixture/out"
cmp "$fixture/in/data" "$fixture/out/data"
INNER
