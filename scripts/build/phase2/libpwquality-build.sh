#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
# Python's unsupported out-of-tree binding is optional; Settings uses the C SDK.
/src/configure --prefix=/usr --libdir=/usr/lib --sysconfdir=/etc --disable-static --disable-python-bindings --enable-pam --with-securedir=/usr/lib/security > /build/original-configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make DESTDIR=/stage install > /build/original-install.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');pc=Path('/stage/usr/lib/pkgconfig/pwquality.pc');assert 'Version: 1.4.5' in pc.read_text()
assert Path('/stage/usr/lib/security/pam_pwquality.so').is_file() and Path('/stage/etc/security/pwquality.conf').is_file()
r={'scope':'Frozen libpwquality1.4.5 shared C SDK/tools/PAM module and stock policy file; supported optional Python bindings omitted, no original test suite per frozen BLFS13.1. Module packaged only: no PAM stack/account/password mutation. No graphical Settings or authentication acceptance.','compile_exit':0,'stage_exit':0,'original_test_suite_available':False,'no_original_suite_not_a_pass':True,'consumer':{'pkgconfig_version':'1.4.5','CLI_tested':False},'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
PY
