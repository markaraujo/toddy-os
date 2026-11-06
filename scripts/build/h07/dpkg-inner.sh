#!/bin/bash
# Frozen supplemental Dpkg source; bootstrap package DB must remain intact.
set -euo pipefail
cd /sources/dpkg-1.22.22
test ! -e /sources/stage/dpkg
mkdir -p /sources/evidence/h07-dpkg
perl_vendor=$(perl -MConfig -e 'print $Config{vendorlib}')
[[ $perl_vendor == /usr/lib/perl5/*/vendor_perl ]]
./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
 --runstatedir=/run --sbindir=/usr/sbin --libexecdir=/usr/lib \
 --with-perllibdir="$perl_vendor" --disable-devel-docs \
 --with-libz --with-libbz2 --with-liblzma --with-libzstd
make
chown -R tester:tester .
su tester -c 'make check' 2>&1 | tee /sources/evidence/h07-dpkg/check.log
make DESTDIR=/sources/stage/dpkg install
# Never package generated dpkg status/locks or replace the populated database.
python3 - <<'PY'
from pathlib import Path
import json
stage=Path('/sources/stage/dpkg');removed=[]
state=stage/'var/lib/dpkg'
if state.exists():
 for path in state.rglob('*'):
  if path.is_file() or path.is_symlink():
   removed.append('/'+str(path.relative_to(stage)));path.unlink()
log=stage/'var/log/dpkg.log'
if log.exists():removed.append('/var/log/dpkg.log');log.unlink()
Path('/sources/evidence/h07-dpkg/generated-state-excluded.json').write_text(json.dumps(removed,indent=2)+'\n')
PY
mkdir -p /sources/stage/dpkg/usr/share/doc/dpkg
cat COPYING AUTHORS >> /sources/stage/dpkg/usr/share/doc/dpkg/copyright
