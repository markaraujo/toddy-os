#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' python) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
python3 - <<'PYTHON'
import sys,ssl,sqlite3,ctypes,decimal,pyexpat,bz2,lzma,zlib,dbm.gnu,curses,readline
assert sys.version_info[:3]==(3,14,10)
assert ssl.OPENSSL_VERSION.startswith('OpenSSL 4.0.3 '), ssl.OPENSSL_VERSION
assert pyexpat.version_info==(2,10,0)
assert decimal.Decimal('0.1')+decimal.Decimal('0.2')==decimal.Decimal('0.3')
assert sqlite3.connect(':memory:').execute('select 42').fetchone()==(42,)
assert ctypes.CDLL('libc.so.6').getpid()>0
assert bz2.decompress(bz2.compress(b'native'))==b'native'
assert lzma.decompress(lzma.compress(b'native'))==b'native'
print('PYTHON_NATIVE_OK')
PYTHON
python3 -m pip --version

INNER
