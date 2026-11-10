#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
cmake -S /src -B /build/compile -G Ninja -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR=lib \
 -DCMAKE_BUILD_TYPE=Release -DCMAKE_SKIP_INSTALL_RPATH=ON -DBUILD_SHARED_LIBS=ON \
 -DEXIV2_ENABLE_XMP=ON -DEXIV2_ENABLE_PNG=ON -DEXIV2_ENABLE_VIDEO=ON -DEXIV2_ENABLE_BMFF=ON \
 -DEXIV2_ENABLE_BROTLI=ON -DEXIV2_ENABLE_INIH=ON -DEXIV2_ENABLE_WEBREADY=OFF -DEXIV2_ENABLE_CURL=OFF \
 -DEXIV2_BUILD_SAMPLES=OFF -DEXIV2_BUILD_UNIT_TESTS=OFF -DEXIV2_BUILD_FUZZ_TESTS=OFF -DEXIV2_BUILD_DOC=OFF -DCONAN_AUTO_INSTALL=OFF
ninja -C /build/compile -j4
ctest --test-dir /build/compile --show-only=json-v1 > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
w=Path('/build');source=Path('/src');private=w/'private-tests';private.mkdir()
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and not p.is_symlink()}
before={n:hashes(source/n) for n in ['test','tests']}
(private/'src').mkdir();(private/'src/canonmn_int.cpp').symlink_to('/src/src/canonmn_int.cpp')
canon_before=hashlib.sha256((source/'src/canonmn_int.cpp').read_bytes()).hexdigest()
for name in ['test','tests']:shutil.copytree(source/name,private/name,symlinks=True);assert hashes(private/name)==before[name]
registered=json.loads((w/'original-registered-tests.json').read_text());rows=registered['tests'];assert {r['name'] for r in rows}=={'bugfixTests','lensTests','tiffTests','versionTests','regressionTests'}
results=[]
for row in rows:
 command=row['command'];assert command[:3]==['/usr/bin/cmake','-E','env'] and 'EXIV2_BINDIR=/build/compile/bin' in command and command[5]=='runner.py' and next(p['value'] for p in row['properties'] if p['name']=='WORKING_DIRECTORY')=='/src/tests'
 cmd=list(command);log=w/(row['name']+'.log');began=time.monotonic()
 try:
  with log.open('xb') as out:r=subprocess.run(cmd,cwd=private/'tests',stdout=out,stderr=subprocess.STDOUT,timeout=480)
  exit=r.returncode
 except subprocess.TimeoutExpired:exit=None
 results.append({'name':row['name'],'exit':exit,'seconds':round(time.monotonic()-began,3),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
 (w/'original-results.json').write_text(json.dumps(results,indent=2)+'\n')
 if exit is None:break
assert before=={n:hashes(source/n) for n in before} and hashlib.sha256((source/'src/canonmn_int.cpp').read_bytes()).hexdigest()==canon_before
(w/'original-private-fixtures.json').write_text(json.dumps({'scope':'Unmodified original drivers on byte-identical private test/data copy, source immutable; only outputs under private fixture/test/tmp','input_files':sum(len(r) for r in before.values()),'source_before_after_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()},indent=2)+'\n')
assert len(results)==5 and all(r['exit']==0 for r in results),'Retain actual original failures/timeouts; no promotion'
PY
DESTDIR=/stage cmake --install /build/compile
LD_LIBRARY_PATH=/stage/usr/lib python3 /src/toddy-probe.py /stage/usr/bin/exiv2 /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
w=Path('/build');r={'scope':'Frozen Exiv2 local PNG/JPEG/TIFF/BMFF/video/XMP metadata profile; Brotli/INI selected, upstream-default network transports omitted. Original five private CTest drivers, raw nested skips/outcomes retained, own local metadata/refusal/reset only; no GExiv2/LocalSearch/GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':json.loads((w/'original-results.json').read_text()),'consumer':json.loads((w/'native-consumer.json').read_text()),'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts','stage_sha256')}))
PY
