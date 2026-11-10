#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/tree ]]
[[ $(stat -c %d /build) != $(stat -c %d /usr) ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# CUPS generates files in its source layout. Only this private writable copy is
# compiled; the authenticated source alias remains read-only in the sandbox.
python3 - <<'PY'
from pathlib import Path
import shutil
shutil.copytree('/src','/build/tree',symlinks=True,copy_function=shutil.copy)
p=Path('/build/tree/cups/ipp.c');s=p.read_text()
assert 'ipp->current == *attr && ipp->prev && ipp->prev->next == *attr' in s
# The frozen2.4.19 source already contains the book's IPP pointer correction.
p=Path('/build/tree/desktop/cups.desktop.in');s=p.read_text();assert s.count('@CUPS_HTMLVIEW@')==1
p.write_text(s.replace('@CUPS_HTMLVIEW@','firefox'))
PY
cd /build/tree
./configure --prefix=/ --libdir=/usr/lib --with-rundir=/run/cups --with-system-groups=lpadmin --with-cups-user=lp --with-cups-group=lp --with-docdir=/usr/share/cups/doc-2.4.19 --with-pkgconfpath=/usr/lib/pkgconfig --with-tls=gnutls > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
python3 - <<'PYTEST'
from pathlib import Path
import json,os,subprocess,time,tempfile,shutil,shlex
w=Path('/build');results=[]
env=dict(os.environ,LC_ALL='C',LD_LIBRARY_PATH='/build/tree/cups')
def run_local_unit(name,env,log):
 if name!='testfile':return subprocess.run(['make','-C','/build/tree/cups',name],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 # Keep original arguments, cases, fixture and linker; move only its large
 # transient files off persistent scratch into the existing private tmpfs.
 makefile=w/'tree/cups/Makefile';original=makefile.read_text();marker='\t./testfile\n';assert original.count(marker)==1
 with tempfile.TemporaryDirectory(prefix='cups-testfile-',dir='/tmp') as directory:
  fixture=Path(directory)/'testfile.txt';source=Path('/src/cups/testfile.txt');shutil.copyfile(source,fixture)
  assert fixture.read_bytes()==source.read_bytes()
  makefile.write_text(original.replace(marker,'\tcd '+shlex.quote(directory)+' && /build/tree/cups/testfile\n'))
  try:return subprocess.run(['make','-C','/build/tree/cups',name],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120)
  finally:makefile.write_text(original)
for name in ['testarray','testfile','testi18n','testipp','testhttp','testoptions','testpwg','testraster','testppd']:
 start=time.monotonic()
 with (w/(name+'.log')).open('xb') as log:
  result=run_local_unit(name,env,log)
 results.append({'name':name,'exit':result.returncode,'seconds':round(time.monotonic()-start,3)})
 (w/'original-local-tests.json').write_text(json.dumps(results,indent=2)+'\n')
 assert result.returncode==0,name
PYTEST
# Preserve compiled lp/lpadmin policy; only unprivileged staging ownership uses
# tester IDs. Controlled native promotion must apply reviewed service ownership.
make BUILDROOT=/stage CUPS_USER=101 CUPS_GROUP=101 CUPS_PRIMARY_SYSTEM_GROUP=101 install > /build/original-stage.log 2>&1
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib \
   -lcups -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --modversion cups > /build/actual-version.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat
def select_local_results(raw, snmp_log):
 required=['testarray','testfile','testi18n','testipp','testhttp','testoptions','testpwg','testraster','testppd']
 assert [t['name'] for t in raw] in (required,required+['testsnmp'])
 tests=raw[:9];assert all(t['exit']==0 for t in tests)
 diagnostic={'qualified':False,'requires_remote_host':True,'executed':len(raw)==10}
 if diagnostic['executed']:
  assert raw[9]['exit']==1
  assert '_cupsSNMPDefaultCommunity: PASS (public)' in snmp_log and 'Usage: testsnmp [options] host-or-ip [oid ...]' in snmp_log
  diagnostic.update(exit=1,classification='No-host usage refusal; not a remote SNMP pass')
 return tests,diagnostic
w=Path('/build');raw_tests=json.loads((w/'original-local-tests.json').read_text())
tests,diagnostic=select_local_results(raw_tests,(w/'testsnmp.log').read_text() if len(raw_tests)==10 else '')
assert (w/'actual-version.log').read_text().strip()=='2.4.19'
consumer=(w/'local-probe.log').read_text();assert consumer=='CUPS local IPP Unicode/add/find/delete/absent attribute/two recoveries; no server, jobs or printer access\n'
for p in Path('/stage').rglob('*'):assert not p.lstat().st_mode&(stat.S_ISUID|stat.S_ISGID)
r={'scope':'Frozen CUPS2.4.19 default full component build with GnuTLS/PAM/USB; nine original local unit programs and actual local IPP C consumer. Full graphical-bus/server/network/driver printing suite unexecuted, not passing. Staging uses tester ownership only; native service ownership/accounts still require controlled promotion. No scheduler/service activation, printer/job/TLS connection/Settings GUI/physical acceptance.','compile_exit':0,'stage_exit':0,'original_tests':tests,'raw_original_results':raw_tests,'SNMP_remote_diagnostic':diagnostic,'full_original_printing_suite_pending':True,'consumer':consumer,'version':'2.4.19','artifacts':{str(p.relative_to(w/'tree')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'tree').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=512*1024**2
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
