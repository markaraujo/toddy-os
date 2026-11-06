#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" --verify-only Python-3.14.10.tar.xz
python3 - <<'CHECK'
import hashlib,json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-python-recovery.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
assert Path('/var/log/toddy/build/h07-build-resolver.success.json').exists()
base=Path('/mnt/lfs/sources/Python-3.14.10')
assert (base/'python').is_file() and (base/'Makefile').is_file()
assert not Path('/mnt/lfs/sources/stage/python').exists()
expected=json.loads(Path('/mnt/lfs/sources/probes/python-openssl-31410-adapted/runtime-identical.json').read_text())
expected['Lib/test/test_ssl.py']='8e5fa996e2d6223c83536334c7469aafbc655fdb5ed5037218f11619fd67285d'
for name,sha in expected.items():
 assert hashlib.sha256((base/name).read_bytes()).hexdigest()==sha,name
print('Verified compiled-source/test identities and build resolver acceptance')
CHECK
python3 "$SOURCE_TOOL" --verify-only Python-3.14.7-openssl_4-1.patch
python3 "$SOURCE_TOOL" --verify-only Python-3.14.10-openssl_4-1.patch
chroot_run < /opt/toddy-build/scripts/build/h07/python-test-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py python 3.14.10-1 \
 "$LFS/sources/stage/python" --depends 'glibc (>= 2.44-1), openssl, expat, libffi, sqlite, mpdecimal, zlib, bzip2, xz, gdbm, ncurses, readline' --source Python-3.14.10.tar.xz --source Python-3.14.7-openssl_4-1.patch --source Python-3.14.10-openssl_4-1.patch --conffile /etc/pip.conf \
 --recipe /opt/toddy-build/scripts/build/h07/python-test-resume.sh --install
