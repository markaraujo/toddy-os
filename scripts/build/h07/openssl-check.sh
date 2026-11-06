#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' openssl) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
openssl version | grep -F 4.0.3
printf abc | openssl dgst -sha256 | grep -F ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
openssl rand -hex 32 | grep -E '^[0-9a-f]{64}$'
test ! -e /usr/lib/libcrypto.a
INNER
