#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h09/require_gate.py
python3 /opt/toddy-build/scripts/build/h09/boot_config.py \
 "$(blkid -s UUID -o value "$TARGET_ROOT")" \
 "$(blkid -s PARTUUID -o value "$TARGET_ROOT")" | cmp - "$LFS/boot/grub/grub.cfg"
chroot_run <<'INNER'
set -euo pipefail
[[ $(dpkg-query -W -f='${Status} ${Version}' toddy-boot-config) == 'install ok installed 0.1-1' ]]
dpkg-query -S /boot/grub/grub.cfg /etc/toddy/grub.cfg
[[ $(readlink /boot/grub/grub.cfg) == ../../etc/toddy/grub.cfg ]]
grub-script-check /boot/grub/grub.cfg
test -s /boot/vmlinuz-7.1.8-toddy
for module in part_gpt ext2 search_fs_uuid serial linux normal; do
 test -s "/usr/lib/grub/i386-pc/$module.mod"
 test -s "/usr/lib/grub/x86_64-efi/$module.mod"
done
printf 'Measured direct-root configuration owned/syntax checked; bootloader installation and actual boot still pending\n'
INNER
