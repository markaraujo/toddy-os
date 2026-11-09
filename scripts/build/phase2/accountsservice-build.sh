#!/bin/bash
# Preserve tarball basename versioning and bundled, SHA-locked test dependencies.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
from pathlib import Path
import hashlib,shutil,zipfile
source=Path('/src')
for name,sha in [('mocklibc-1.0.tar.gz','b2236a6af1028414783e9734a46ea051916ec226479d6a55a3bb823bff68f120'),('mocklibc-1.0-2-wrap.zip','0280f96a2eeb3c023e5acf4e00cef03d362868218d4a85347ea45137c0ef6c56')]:
 assert hashlib.sha256((source/'subprojects/packagecache'/name).read_bytes()).hexdigest()==sha
with zipfile.ZipFile(source/'subprojects/packagecache/mocklibc-1.0-2-wrap.zip') as z:assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
shutil.copytree(source,'/build/source/accountsservice-26.27.3',symlinks=True)
PY
cd /build/source/accountsservice-26.27.3
[[ $(./generate-version.sh) == 26.27.3 ]]
meson setup /build/compile . --prefix=/usr --libdir=lib --libexecdir=libexec \
    --sysconfdir=/etc --localstatedir=/var --buildtype=release --wrap-mode=nodownload \
    -Dintrospection=true -Dvapi=false -Dtests=true -Dgtk_doc=false -Ddocbook=false \
    -Dadmin_group=wheel -Dlibxcrypt=true -Dcreate_homed=false -Dwtmpfile=/var/log/wtmp
ninja -C /build/compile -j4
# One original test requires this locale; generate private data, no system update.
mkdir /build/locale-fixture
localedef --no-archive -i en_IE -f UTF-8 /build/locale-fixture/en_IE.UTF-8
export LOCPATH=/build/locale-fixture
python3 - <<'PY'
from pathlib import Path
import json,subprocess
p=Path('/build');rows=json.loads((p/'compile/meson-info/intro-tests.json').read_text());selected=[r['name'] for r in rows if r['name']!='check-format']
assert len(selected)>=3 and any('util'==r for r in selected)
with (p/'original-tests.log').open('x') as log:
 r=subprocess.run(['meson','test','-C',str(p/'compile'),'--no-rebuild','--print-errorlogs','-j2',*selected],stdout=log,stderr=subprocess.STDOUT)
(p/'original-tests.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
PY
meson install -C /build/compile --destdir /stage --no-rebuild --skip-subprojects
export LD_LIBRARY_PATH=/stage/usr/lib
export GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0
python3 /src/toddy-probe.py /stage > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,re
p=Path('/build');registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());selected=[r for r in registered if r['name']!='check-format'];rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert len(rows)==len(selected) and len(rows)>=3
records=[]
for r in rows:
 assert r['result']=='OK' and r['returncode']==0
 text=r.get('stdout','')+'\n'+r.get('stderr','');assert 'Skipping tests' not in text
 match=re.search(r'Ran (\d+) tests?',text)
 records.append({'name':r['name'],'exit':0,'unittest_cases':int(match.group(1)) if match else None,'observed_tap_pass_lines':len(re.findall(r'^ok \d+',text,re.M)),'unittest_skip_summary':re.findall(r'OK \(skipped=\d+\)',text)})
assert any(r['unittest_cases'] for r in records),'Missing real original Python executions'
result={'scope':'Original AccountsService client/daemon fixture tests and native CLI/GI; fixtures use mocklibc/mock bus, NOT real account/privilege/GDM acceptance','compile_exit':0,'stage_exit':0,'source_version':'26.27.3','selected_original_programs':len(records),'original_tests':records,'excluded':'Unchanged-source check-format lint, not a runtime pass; optional Vala/doc/homed not selected','consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert not any('mocklibc' in name for name in result['stage_sha256'])
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
