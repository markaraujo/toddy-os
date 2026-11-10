#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
[[ $(stat -c %d /build) != $(stat -c %d /usr) ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/src/configure --prefix=/usr --libdir=/usr/lib --sysconfdir=/etc --localstatedir=/var/lib --runstatedir=/run --with-system-et --with-system-ss --with-system-verto=no --enable-dns-for-realm --disable-rpath > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make -j1 -C lib/crypto/crypto_tests check-unix > /build/original-crypto-tests.log 2>&1
# The shared make check-unix target also starts the complete Python realm suite.
# Run these five unchanged original local C tests directly with its RUN_TEST env.
python3 - <<'PYGSS'
from pathlib import Path
import os,subprocess
w=Path('/build');env=dict(os.environ,LD_LIBRARY_PATH='/build/compile/lib',KRB5_CONFIG='/src/src/config-files/krb5.conf',LC_ALL='C')
with (w/'original-gss-c-tests.log').open('xb') as log:
 for name in ['t_invalid','t_oid','t_prf','t_imp_name','reload']:
  log.write((name+'\n').encode());log.flush()
  subprocess.run(['./'+name],cwd=w/'compile/tests/gssapi',env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=30)
PYGSS
make -j1 -C plugins/kdb/db2/libdb2/test check > /build/original-db2-tests.log 2>&1
make DESTDIR=/stage 'INSTALL_SETUID=$(INSTALL_PROGRAM)' install > /build/original-stage.log 2>&1
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib \
   $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs krb5) -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --modversion krb5 > /build/actual-version.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat,re
w=Path('/build');assert (w/'actual-version.log').read_text().strip()=='1.22.2'
consumer=(w/'local-probe.log').read_text();assert consumer=='Kerberos local principal/MEMORY cache reopen/destroy/realm and absent-principal refusals/two recoveries; no tickets or network authentication\n'
for p in Path('/stage').rglob('*'):assert not p.lstat().st_mode&(stat.S_ISUID|stat.S_ISGID)
logs={n:{'exit':0,'log':file,'sha256':hashlib.sha256((w/file).read_bytes()).hexdigest()} for n,file in [('crypto','original-crypto-tests.log'),('gss','original-gss-c-tests.log'),('db2','original-db2-tests.log')]}
db2_cases=re.findall(r'^Test ([0-9]+): (.+)$',(w/'original-db2-tests.log').read_text(),re.M);assert {int(n) for n,_ in db2_cases}==set(list(range(1,12))+[13,20,40,41,50,60,61,62,63])
db2_skipped=[{'case':int(n),'reason':reason} for n,reason in db2_cases if 'skipped' in reason]
r={'scope':'Frozen MIT Kerberos1.22.2 with all3 required frozen upstream/security/OpenSSL4 patches, original local crypto check-unix/five GSS C tests and bundled DB2 check (book test12 exclusion). Own real principal/MEMORY-cache/refusal/recovery API. Full network/realm/Python/provider/enterprise login suite not executed. No owner credentials/tickets/realm authentication/daemon/Settings GUI/physical acceptance.','compile_exit':0,'stage_exit':0,'original_selected_tests':logs,'DB2_report_rows':len(db2_cases),'DB2_unique_case_ids':sorted({int(n) for n,_ in db2_cases}),'DB2_skipped':db2_skipped,'DB2_book_test12_excluded':True,'consumer':consumer,'version':'1.22.2','artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=512*1024**2
PY
