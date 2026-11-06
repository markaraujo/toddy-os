#!/bin/bash
# Prepared LFS 13.1 section 10.3 recipe; H08 acceptance is mandatory.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h09/require_gate.py
python3 "$SOURCE_TOOL" --verify-only linux-7.1.8.tar.xz
python3 - <<'PY'
from pathlib import Path
from datetime import datetime,timezone
import json
source=Path('/mnt/lfs/sources/linux-7.1.8')
if source.exists():
 assert not source.is_symlink() and source.resolve()==source
 assert (source/'usr/include/linux/version.h').is_file(),'Unexpected retained kernel source'
 assert not (source/'.config').exists() and not (source/'vmlinux').exists(),'Inspect existing kernel build for recovery'
 accepted=json.loads(Path('/var/log/toddy/build/h07-linux-api-headers.success.json').read_text())
 assert accepted['recipe_exit']==0 and accepted['postcheck_exit']==0
 recovery=source.parent/'recovery'
 assert not recovery.is_symlink()
 recovery.mkdir(exist_ok=True)
 destination=recovery/('linux-api-build-before-h09-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
 source.rename(destination)
 print('Preserved API-header source/build state:',destination)
PY
cd "$LFS/sources"
python3 "$SOURCE_TOOL" linux-7.1.8.tar.xz
mkdir -p "$LFS/sources/evidence/h09-kernel"
cp /opt/toddy-build/config/kernel.config.fragment "$LFS/sources/evidence/h09-kernel/requested.config"
chroot_run <<'INNER'
set -euo pipefail
cd /sources/linux-7.1.8
test ! -e /sources/stage/linux-kernel
make mrproper
make x86_64_defconfig
scripts/kconfig/merge_config.sh -m .config /sources/evidence/h09-kernel/requested.config
make olddefconfig
INNER
python3 /opt/toddy-build/scripts/build/h09/check_kernel_config.py \
 "$LFS/sources/evidence/h09-kernel/requested.config" "$LFS/sources/linux-7.1.8/.config" \
 --source "$LFS/sources/linux-7.1.8" | tee "$LFS/sources/evidence/h09-kernel/configuration.json"
chroot_run <<'INNER'
set -euo pipefail
cd /sources/linux-7.1.8
export KBUILD_BUILD_USER=toddy KBUILD_BUILD_HOST=builder KBUILD_BUILD_VERSION=1
export KBUILD_BUILD_TIMESTAMP='2026-11-05 00:00:00 UTC'
# kernelrelease deliberately skips config synchronization. Refresh auto.conf
# after merging the fragment before checking the requested local version.
make prepare
release=$(make -s kernelrelease)
[[ $release == 7.1.8-toddy ]]
stage=/sources/stage/linux-kernel
make
make INSTALL_MOD_PATH="$stage" modules_install
# Image assembly excludes /sources. Do not ship links to its build tree.
for link in "$stage/lib/modules/$release/build" "$stage/lib/modules/$release/source"; do
 if [[ -e $link || -L $link ]]; then
  [[ -L $link && $(readlink "$link") == /sources/linux-7.1.8 ]]
  rm "$link"
 fi
done
depmod -b "$stage" "$release"
install -Dm644 arch/x86/boot/bzImage "$stage/boot/vmlinuz-$release"
install -Dm644 System.map "$stage/boot/System.map-$release"
install -Dm644 .config "$stage/boot/config-$release"
mkdir -p "$stage/usr/share/doc/linux-kernel"
cp COPYING "$stage/usr/share/doc/linux-kernel/copyright"
cp -a LICENSES Documentation "$stage/usr/share/doc/linux-kernel/"
cp .config /sources/evidence/h09-kernel/resolved.config
cc --version > /sources/evidence/h09-kernel/compiler.txt
sha256sum arch/x86/boot/bzImage System.map .config > /sources/evidence/h09-kernel/build-hashes.txt
chown -R 0:0 /sources/linux-7.1.8
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py linux-kernel 7.1.8-1 \
 "$LFS/sources/stage/linux-kernel" --depends 'kmod, filesystem-layout' \
 --source linux-7.1.8.tar.xz --recipe /opt/toddy-build/scripts/build/h09/kernel.sh --install
