#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" --verify-only Python-3.14.10.tar.xz
python3 - <<'CHECK'
import json,tarfile
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-python.failed.json').read_text())
assert r['recipe_exit']==1 and r['changed_paths']==0
base=Path('/mnt/lfs/sources')
assert not (base/'stage/python').exists()
for name in ['Makefile','config.log','pyconfig.h']:
 assert not (base/'Python-3.14.10'/name).exists()
checked=0
with tarfile.open(base/'Python-3.14.10.tar.xz') as archive:
 for member in archive.getmembers():
  if member.isfile():
   assert (base/member.name).read_bytes()==archive.extractfile(member).read(), member.name
   checked+=1
assert checked>1000
print('Verified untouched original Python source files:',checked)
CHECK
python3 "$SOURCE_TOOL" --verify-only Python-3.14.7-openssl_4-1.patch
python3 "$SOURCE_TOOL" --verify-only Python-3.14.10-openssl_4-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/python-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py python 3.14.10-1 \
 "$LFS/sources/stage/python" --depends 'glibc (>= 2.44-1), openssl, expat, libffi, sqlite, mpdecimal, zlib, bzip2, xz, gdbm, ncurses, readline' --source Python-3.14.10.tar.xz --source Python-3.14.7-openssl_4-1.patch --source Python-3.14.10-openssl_4-1.patch --conffile /etc/pip.conf \
 --recipe /opt/toddy-build/scripts/build/h07/python-resume.sh --install
