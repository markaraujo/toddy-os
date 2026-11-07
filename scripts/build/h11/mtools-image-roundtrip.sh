#!/bin/bash
# Native tool behavior and a real GRUB EFI binary; private image files only.
set -euo pipefail
export LC_ALL=C.UTF-8 MTOOLSRC=/dev/null
mformat --version | grep -F '4.0.50'
work=$(mktemp -d /tmp/toddy-native-fat-image.XXXXXX)
cleanup() {
 result=$?
 if [[ $result == 0 ]]; then rm -rf -- "$work"; else printf 'Preserved failed FAT fixture: %s\n' "$work" >&2; fi
 exit "$result"
}
trap cleanup EXIT
mkdir -p "$work/EFI/BOOT"
grub-mkimage -O x86_64-efi -o "$work/EFI/BOOT/BOOTX64.EFI" -p /boot/grub part_gpt fat normal
grub-file --is-x86_64-efi "$work/EFI/BOOT/BOOTX64.EFI"
# Match the frozen grub-mkrescue.c invocation, including geometry/FAT length.
mformat -C -f 2880 -L 16 -i "$work/efi.img" ::
mcopy -s -i "$work/efi.img" "$work/EFI" ::/
mdir -i "$work/efi.img" ::/EFI/BOOT
mcopy -i "$work/efi.img" ::/EFI/BOOT/BOOTX64.EFI "$work/restored.efi"
cmp "$work/EFI/BOOT/BOOTX64.EFI" "$work/restored.efi"
grub-file --is-x86_64-efi "$work/restored.efi"
printf 'Native FAT long UTF-8 filename roundtrip\n' > "$work/ação longa.txt"
mcopy -i "$work/efi.img" "$work/ação longa.txt" '::/EFI/BOOT/ação longa.txt'
mcopy -i "$work/efi.img" '::/EFI/BOOT/ação longa.txt' "$work/restored.txt"
cmp "$work/ação longa.txt" "$work/restored.txt"
printf 'This is not a FAT filesystem\n' > "$work/invalid.img"
set +e
timeout 10 mdir -i "$work/invalid.img" :: > "$work/negative.log" 2>&1
result=$?
set -e
cat "$work/negative.log"
[[ $result -gt 0 && $result -lt 124 ]]
sha256sum "$work/efi.img" "$work/EFI/BOOT/BOOTX64.EFI" "$work/restored.efi"
printf 'NATIVE_MTOOLS_FAT_IMAGE_ACCEPTED: EFI bytes, recursive copy, UTF-8 and invalid-image refusal; boot not tested\n'
