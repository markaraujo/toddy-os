#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only gnupg-2.5.24.tar.bz2
python3 - <<'CHECK'
from pathlib import Path
import hashlib,json,tarfile
r=json.loads(Path('/var/log/toddy/build/h07-gnupg.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
base=Path('/mnt/lfs/sources');source=base/'gnupg-2.5.24'
assert not (base/'stage/gnupg').exists() and not (source/'build-without-cms').exists()
assert 'FAIL: tests/cms/setup.scm' in (base/'evidence/h07-gnupg/check.log').read_text()
with tarfile.open(base/'gnupg-2.5.24.tar.bz2') as archive:
 for member in archive.getmembers():
  if member.isfile():
   actual=base/member.name
   assert actual.is_file() and not actual.is_symlink(),member.name
   assert hashlib.sha256(actual.read_bytes()).digest()==hashlib.sha256(archive.extractfile(member).read()).digest(),member.name
print('All original authenticated GnuPG source bytes remain unchanged')
CHECK
mkdir -p "$LFS/sources/evidence/h07-gnupg/initial-disabled-cms"
cp "$LFS/sources/evidence/h07-gnupg/check.log" "$LFS/sources/evidence/h07-gnupg/initial-disabled-cms/"
mv "$LFS/sources/gnupg-2.5.24/build" "$LFS/sources/gnupg-2.5.24/build-without-cms"
chroot_run < /opt/toddy-build/scripts/build/h07/gnupg-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py gnupg 2.5.24-1 \
 "$LFS/sources/stage/gnupg" --depends 'glibc (>= 2.44-1), libgpg-error, libgcrypt, libassuan, libksba, npth, zlib, bzip2, readline' --source gnupg-2.5.24.tar.bz2 \
 --recipe /opt/toddy-build/scripts/build/h07/gnupg-resume.sh --install
