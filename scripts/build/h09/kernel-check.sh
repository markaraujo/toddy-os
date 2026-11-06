#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 /opt/toddy-build/scripts/build/h09/require_gate.py
python3 /opt/toddy-build/scripts/build/h09/check_kernel_config.py \
 /opt/toddy-build/config/kernel.config.fragment "$LFS/boot/config-7.1.8-toddy" \
 --source "$LFS/sources/linux-7.1.8"
chroot_run <<'INNER'
set -euo pipefail
dpkg-query -S /boot/vmlinuz-7.1.8-toddy /boot/config-7.1.8-toddy
grub-file --is-x86-linux /boot/vmlinuz-7.1.8-toddy
grub-file --is-x86_64-efi /boot/vmlinuz-7.1.8-toddy
modinfo -k 7.1.8-toddy -F vermagic dummy | grep -F '7.1.8-toddy '
test ! -e /usr/lib/modules/7.1.8-toddy/build
test ! -L /usr/lib/modules/7.1.8-toddy/build
test ! -e /usr/lib/modules/7.1.8-toddy/source
test ! -L /usr/lib/modules/7.1.8-toddy/source
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
files={}
for name in ['vmlinuz','System.map','config']:
 path=Path('/boot')/(name+'-7.1.8-toddy')
 with path.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
 files[str(path)]={'size':path.stat().st_size,'sha256':sha}
module=Path(subprocess.check_output(['modinfo','-k','7.1.8-toddy','-n','dummy'],text=True).strip())
assert module.is_file() and module.resolve().is_relative_to('/usr/lib/modules/7.1.8-toddy')
Path('/sources/evidence/h09-kernel/installed-artifacts.json').write_text(json.dumps({'files':files,'dummy_module':str(module),'boot_validated':False,'hardware_support_claimed':False},indent=2)+'\n')
PY
printf 'Kernel artifacts/config/module metadata checked; boot and module loading remain separate gates\n'
INNER
