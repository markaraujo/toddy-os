#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' grub) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
test -s /usr/lib/grub/i386-pc/normal.mod
test -s /usr/lib/grub/x86_64-efi/normal.mod
grub-mkimage -O i386-pc -p /boot/grub -o /tmp/toddy-bios-core.img biosdisk part_gpt ext2 normal
grub-mkimage -O x86_64-efi -p /boot/grub -o /tmp/toddy-efi.img part_gpt ext2 normal
grub-file --is-x86_64-efi /tmp/toddy-efi.img
test -s /tmp/toddy-bios-core.img
rm /tmp/toddy-{bios-core,efi}.img
INNER
