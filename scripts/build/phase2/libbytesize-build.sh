#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
python3 - <<'PYTEST'
from pathlib import Path
import json,os,subprocess,re
w=Path('/build');results=[]
env=dict(os.environ,LC_ALL='C.UTF-8',PYTHONPATH='/src/src/python',LD_LIBRARY_PATH='/build/compile/src/.libs')
locales=subprocess.check_output(['locale','-a'],env=env,text=True).split()
assert 'en_US.utf8' in locales,'Original default suite must execute; do not accept all-skipped fixtures'
commands=[('core',['python3','/src/tests/libbytesize_unittest.py']),('override',['python3','/src/tests/lbs_py_override_unittest.py','-v'])]
if 'fr_FR.utf8' in locales:commands.append(('core-fr',['python3','/src/tests/libbytesize_unittest.py','fr_FR.UTF-8']))
for name,command in commands:
 with (w/('original-'+name+'.log')).open('xb') as log:result=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
 text=(w/('original-'+name+'.log')).read_text();count=re.search(r'Ran ([0-9]+) tests?',text)
 skipped=re.search(r'skipped=([0-9]+)',text);skipped_count=int(skipped.group(1)) if skipped else 0
 results.append({'skipped_count':skipped_count,'name':name,'exit':result.returncode,'cases':int(count.group(1)) if count else None,'log':'original-'+name+'.log','skips':[l for l in text.splitlines() if 'skipped' in l]})
 (w/'original-tests.json').write_text(json.dumps(results,indent=2)+'\n')
 assert result.returncode==0 and count and int(count.group(1))>skipped_count and '\nOK' in text,name
(w/'test-selection.json').write_text(json.dumps({'original_selected_programs':results,'locale_inventory':locales,'fr_suite_available':'fr_FR.utf8' in locales,'translation_canary_pending':'Optional pocketlint/polib translation-only program not selected; not a full original-suite pass'},indent=2)+'\n')
PYTEST
make DESTDIR=/stage install > /build/original-stage.log 2>&1
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -Wl,-rpath-link,/stage/usr/lib -lbytesize -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
export LD_LIBRARY_PATH=/stage/usr/lib PYTHONPATH=/stage/usr/lib/python3.14/site-packages
python3 - <<'PYPY' > /build/python-consumer.log
from bytesize import Size,InvalidSpecError
for cycle in range(2):
 assert int(Size('1 GiB')+Size('512 MiB'))==1610612736
 try:Size('not a size')
 except ValueError as error:assert isinstance(error.args[0],InvalidSpecError)
 else:raise AssertionError('Malformed specification accepted')
 assert int(Size('1 KiB'))==1024
print('Python exact size arithmetic/malformed refusal/two recoveries')
PYPY
/stage/usr/bin/bscalc -b '1 GiB + 512 MiB' </dev/null > /build/cli-result.log
PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --modversion bytesize > /build/actual-version.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat
w=Path('/build');assert (w/'actual-version.log').read_text().strip()=='2.12'
assert (w/'cli-result.log').read_text().strip()=='1610612736 B'
assert (w/'python-consumer.log').read_text()=='Python exact size arithmetic/malformed refusal/two recoveries\n'
consumer=(w/'local-probe.log').read_text();assert consumer=='Libbytesize exact binary units/add/divide/big integer/invalid specification/zero division/overflow/two recoveries; no disk access\n'
for p in Path('/stage').rglob('*'):assert not p.lstat().st_mode&(stat.S_ISUID|stat.S_ISGID)
r={'scope':'Frozen libbytesize2.12 shared C/Python/bscalc default profile, original selected core/override plus available default French run; actual case skips remain explicit. Optional translation-canary pending. Exact local unit arithmetic/errors/recovery only; no UDisks/blockdev/service/disk/Settings GUI/hardware acceptance.','compile_exit':0,'stage_exit':0,'original_tests':json.loads((w/'original-tests.json').read_text()),'test_selection':json.loads((w/'test-selection.json').read_text()),'consumer':consumer,'python_consumer':(w/'python-consumer.log').read_text(),'CLI':(w/'cli-result.log').read_text(),'version':'2.12','artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
