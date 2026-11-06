#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only xxHash-0.8.4.tar.gz
python3 - <<'CHECK'
from pathlib import Path
import hashlib,json,tarfile
r=json.loads(Path('/var/log/toddy/build/h07-xxhash.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
assert Path('/var/log/toddy/build/h07-time.success.json').exists()
base=Path('/mnt/lfs/sources');assert not (base/'stage/xxhash').exists()
assert 'time: No such file or directory' in (base/'evidence/h07-xxhash/check.log').read_text()
with tarfile.open(base/'xxHash-0.8.4.tar.gz') as archive:
 for member in archive.getmembers():
  if member.isfile():
   actual=base/member.name
   assert actual.is_file() and not actual.is_symlink(),member.name
   assert hashlib.sha256(actual.read_bytes()).digest()==hashlib.sha256(archive.extractfile(member).read()).digest(),member.name
print('Original XXHash source bytes remain unchanged before complete retry')
CHECK
chroot_run < /opt/toddy-build/scripts/build/h07/xxhash-test-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py xxhash 0.8.4-1 \
 "$LFS/sources/stage/xxhash" --depends 'glibc (>= 2.44-1)' --source xxHash-0.8.4.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/xxhash-test-resume.sh --install
