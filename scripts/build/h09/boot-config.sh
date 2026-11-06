#!/bin/bash
# LFS 13.1 section 10.4: package only the measured direct-root configuration.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h09/require_gate.py
python3 - <<'PY'
import json
from pathlib import Path
result=json.loads(Path('/var/log/toddy/build/h09-kernel.success.json').read_text())
assert result['recipe_exit']==0 and result['postcheck_exit']==0
PY
stage="$LFS/sources/stage/toddy-boot-config"
[[ ! -e $stage && ! -L $stage ]]
[[ $(lsblk -dn -o PTTYPE "$TARGET_DISK") == gpt ]]
filesystem_uuid=$(blkid -s UUID -o value "$TARGET_ROOT")
partition_uuid=$(blkid -s PARTUUID -o value "$TARGET_ROOT")
mkdir -p "$stage/boot/grub" "$stage/etc/toddy" "$stage/usr/share/doc/toddy-boot-config"
python3 /opt/toddy-build/scripts/build/h09/boot_config.py "$filesystem_uuid" "$partition_uuid" > "$stage/etc/toddy/grub.cfg"
# Keep mutable configuration under the existing /etc conffile policy.
# GRUB follows the relative ext4 symlink from its standard configuration path.
ln -s ../../etc/toddy/grub.cfg "$stage/boot/grub/grub.cfg"
cp /opt/toddy-build/LICENSES/LFS-MIT.txt "$stage/usr/share/doc/toddy-boot-config/copyright"
chroot_run <<'INNER'
set -euo pipefail
grub-script-check /sources/stage/toddy-boot-config/etc/toddy/grub.cfg
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py toddy-boot-config 0.1-1 "$stage" \
 --architecture all --depends 'grub, linux-kernel' --conffile /etc/toddy/grub.cfg \
 --recipe /opt/toddy-build/scripts/build/h09/boot-config.sh --install
