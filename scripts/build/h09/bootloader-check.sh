#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h09/require_gate.py
bash /opt/toddy-build/scripts/build/h09/boot-config-check.sh
[[ $(lsblk -dn -o PKNAME /dev/vdb2) == vdb ]]
[[ $(blkid -s LABEL -o value /dev/vdb2) == TODDY_ESP ]]
[[ $(realpath "$LFS/boot/efi") == "$LFS/boot/efi" ]]
[[ -z $(findmnt -n -o TARGET --source /dev/vdb2) ]]
mountpoint -q "$LFS/boot/efi" && exit 1
mount -o ro -t vfat /dev/vdb2 "$LFS/boot/efi"
trap 'result=$?; trap - EXIT; umount "$LFS/boot/efi" || result=$?; exit "$result"' EXIT
python3 /opt/toddy-build/scripts/build/h09/boot_manifest.py check
chroot_run <<'INNER'
set -euo pipefail
grub-file --is-x86_64-efi /boot/efi/EFI/BOOT/BOOTX64.EFI
grub-script-check /boot/grub/grub.cfg
INNER
