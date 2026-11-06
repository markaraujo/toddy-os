#!/bin/bash
# LFS 13.1 section 10.4, confined to the designated disposable target disk.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h09/require_gate.py
python3 - <<'PY'
import json
from pathlib import Path
for step in ('kernel','boot-config'):
 result=json.loads((Path('/var/log/toddy/build')/('h09-'+step+'.success.json')).read_text())
 assert result['recipe_exit']==0 and result['postcheck_exit']==0,step
PY
bash /opt/toddy-build/scripts/build/h09/boot-config-check.sh
[[ $(lsblk -dn -o PTTYPE "$TARGET_DISK") == gpt ]]
[[ $(lsblk -dn -o PKNAME /dev/vdb1) == vdb ]]
[[ $(lsblk -dn -o PARTTYPE /dev/vdb1) == 21686148-6449-6e6f-744e-656564454649 ]]
[[ -z $(lsblk -dn -o FSTYPE /dev/vdb1) ]]
[[ $(blockdev --getsize64 /dev/vdb1) -ge 1048576 ]]
[[ $(blockdev --getsize64 /dev/vdb1) -le 8388608 ]]
[[ $(lsblk -dn -o PKNAME /dev/vdb2) == vdb ]]
[[ $(lsblk -dn -o PARTTYPE /dev/vdb2) == c12a7328-f81f-11d2-ba4b-00a0c93ec93b ]]
[[ $(blkid -s TYPE -o value /dev/vdb2) == vfat ]]
[[ $(blkid -s LABEL -o value /dev/vdb2) == TODDY_ESP ]]
[[ $(realpath "$LFS/boot") == "$LFS/boot" ]]
[[ ! -L $LFS/boot/efi ]]
[[ ! -e $LFS/boot/grub/i386-pc && ! -e $LFS/boot/grub/x86_64-efi ]]
[[ ! -L $LFS/boot/grub/i386-pc && ! -L $LFS/boot/grub/x86_64-efi ]]
evidence="$LFS/sources/evidence/h09-bootloader"
[[ $(realpath -m "$evidence") == "$evidence" ]]
[[ ! -e $evidence && ! -L $evidence ]] || { echo 'Preserve/diagnose previous bootloader attempt before retry';exit 1; }
[[ -z $(findmnt -n -o TARGET --source /dev/vdb2) ]]
mkdir -p "$LFS/boot/efi"
mountpoint -q "$LFS/boot/efi" && exit 1
[[ -z $(find "$LFS/boot/efi" -mindepth 1 -print -quit) ]]
mounted=0
cleanup() {
 result=$?
 trap - EXIT
 if [[ $mounted == 1 ]]; then umount "$LFS/boot/efi" || result=$?;fi
 exit "$result"
}
trap cleanup EXIT
mount -t vfat /dev/vdb2 "$LFS/boot/efi"
mounted=1
[[ $(findmnt -n -o SOURCE --mountpoint "$LFS/boot/efi") == /dev/vdb2 ]]
# Initial installation only. Preserve unexpected existing EFI payload for review.
[[ -z $(find "$LFS/boot/efi" -mindepth 1 -type f -print -quit) ]]
mkdir -m700 "$evidence"
dd if="$TARGET_DISK" of="$evidence/first-mib.before.bin" bs=1M count=1 status=none
dd if=/dev/vdb1 of="$evidence/bios-partition.before.bin" bs=1M status=none
sfdisk --dump "$TARGET_DISK" > "$evidence/partition-table.before.txt"
sha256sum "$LFS/etc/toddy/grub.cfg" "$LFS/boot/vmlinuz-7.1.8-toddy" > "$evidence/owned-boot-inputs.sha256"
# Repeat target identity immediately before the boot-sector operation.
guard_target
chroot_run <<'INNER'
set -euo pipefail
grub-install /dev/vdb --target=i386-pc --boot-directory=/boot --recheck
grub-install --target=x86_64-efi --efi-directory=/boot/efi --boot-directory=/boot --removable --no-nvram --recheck
grub-file --is-x86_64-efi /boot/efi/EFI/BOOT/BOOTX64.EFI
grub-script-check /boot/grub/grub.cfg
INNER
sha256sum -c "$evidence/owned-boot-inputs.sha256"
sfdisk --dump "$TARGET_DISK" > "$evidence/partition-table.after.txt"
cmp "$evidence/partition-table.before.txt" "$evidence/partition-table.after.txt"
python3 /opt/toddy-build/scripts/build/h09/boot_manifest.py write
sync
