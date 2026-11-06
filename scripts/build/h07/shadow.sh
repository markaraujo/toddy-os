#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" shadow-4.20.2.tar.xz
chroot_run < /opt/toddy-build/scripts/build/h07/shadow-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py shadow 4.20.2-1 \
 "$LFS/sources/stage/shadow" --depends 'glibc (>= 2.44-1), libxcrypt' \
 --source shadow-4.20.2.tar.xz --conffile /etc/login.defs \
 --recipe /opt/toddy-build/scripts/build/h07/shadow.sh --install
chroot_run <<'INNER'
set -euo pipefail
pwconv
grpconv
mkdir -p /etc/default
useradd -D --gid 999
sed -i '/MAIL/s/yes/no/' /etc/default/useradd
touch /etc/sub{u,g}id
# H08 establishes an ephemeral VM login strategy; lock root until then.
passwd -l root
INNER
rm -rf "$LFS/sources/shadow-4.20.2"
