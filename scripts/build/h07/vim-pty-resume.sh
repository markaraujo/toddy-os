#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only vim-9.2.1201.tar.gz
python3 - <<'CHECK'
from pathlib import Path
import hashlib,json,tarfile
r=json.loads(Path('/var/log/toddy/build/h07-vim-recovery.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
base=Path('/mnt/lfs/sources');assert not (base/'stage/vim').exists()
with tarfile.open(base/'vim-9.2.1201.tar.gz') as archive:
 for member in archive.getmembers():
  if member.isfile() and Path(member.name).suffix in ['.c','.h','.vim'] and '/src/auto/' not in member.name:
   expected=archive.extractfile(member).read()
   if member.name.endswith('/src/feature.h'):expected+=b'#define SYS_VIMRC_FILE "/etc/vimrc"\n'
   actual=base/member.name
   assert actual.is_file() and not actual.is_symlink(),member.name
   assert hashlib.sha256(actual.read_bytes()).digest()==hashlib.sha256(expected).digest(),member.name
print('Original Vim code/test identities verified, with only book vimrc definition')
CHECK
chroot_run < /opt/toddy-build/scripts/build/h07/vim-pty-test-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py vim 9.2.1201-1 \
 "$LFS/sources/stage/vim" --depends 'glibc (>= 2.44-1), ncurses' --source vim-9.2.1201.tar.gz \
 --conffile /etc/vimrc --recipe /opt/toddy-build/scripts/build/h07/vim-pty-resume.sh --install
