#!/bin/bash
# Private native filesystem probe only: no block device, mount or boot install.
set -euo pipefail
work=$(mktemp -d /tmp/toddy-grub-config-link.XXXXXX)
trap 'rm -rf -- "$work"' EXIT
printf 'set default=0\nset timeout=5\n' > "$work/expected.cfg"
truncate -s 16M "$work/private.ext4"
mkfs.ext4 -q -F "$work/private.ext4"
for directory in /boot /boot/grub /etc /etc/toddy; do
 debugfs -w -R "mkdir $directory" "$work/private.ext4" > "$work/debugfs.log" 2>&1
done
debugfs -w -R "write $work/expected.cfg /etc/toddy/grub.cfg" "$work/private.ext4" >> "$work/debugfs.log" 2>&1
debugfs -w -R 'symlink /boot/grub/grub.cfg ../../etc/toddy/grub.cfg' "$work/private.ext4" >> "$work/debugfs.log" 2>&1
grub-fstest "$work/private.ext4" cat /boot/grub/grub.cfg > "$work/observed.cfg"
cmp "$work/expected.cfg" "$work/observed.cfg"
grub-script-check "$work/observed.cfg"
printf 'NATIVE_GRUB_EXT4_RELATIVE_CONFIGURATION_LINK_ACCEPTED; private regular-file image only; no boot claimed\n'
