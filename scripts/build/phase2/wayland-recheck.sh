#!/bin/bash
# Only the failed outer tests after the standard FD alias correction; no rebuild.
set -euo pipefail
[[ $(id -u) == 101 ]]
ulimit -c 0
export XDG_RUNTIME_DIR=/build/runtime
python3 - <<'PRE'
import hashlib,json,shutil
from pathlib import Path
logs=Path('/build/compile/meson-logs');dest=Path('/build/failed-tests-1')
assert not dest.exists(),'Inspect prior recheck; do not overwrite failed logs'
shutil.copytree(logs,dest)
rows=[json.loads(line) for line in (dest/'testlog.json').read_text().splitlines()]
assert len(rows)==26 and sum(row['result']=='OK' for row in rows)==6 and sum(row['result']=='FAIL' for row in rows)==20
files={}
for row in rows:
    path=Path(row['command'][0])
    if path.is_file():files[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
files['/build/compile/src/wayland-scanner']=hashlib.sha256(Path('/build/compile/src/wayland-scanner').read_bytes()).hexdigest()
Path('/build/recheck-input-binaries.json').write_text(json.dumps(files,indent=2)+'\n')
Path('/build/failed-tests-names.txt').write_text('\n'.join(row['name'].split(':')[-1] for row in rows if row['result']=='FAIL')+'\n')
PRE
mapfile -t failed < /build/failed-tests-names.txt
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4 "${failed[@]}"
DESTDIR=/stage ninja -C /build/compile install
python3 - <<'POST'
import hashlib,json
from pathlib import Path
old=[json.loads(line) for line in Path('/build/failed-tests-1/testlog.json').read_text().splitlines()]
new=[json.loads(line) for line in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(new)==20 and all(row['result']=='OK' and row['returncode']==0 and not row['is_fail'] for row in new)
assert {r['name'] for r in new}=={r['name'] for r in old if r['result']=='FAIL'}
files=json.loads(Path('/build/recheck-input-binaries.json').read_text())
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha for path,sha in files.items()),'Do not reuse evidence after changed binaries'
Path('/build/qualified-tests.json').write_text(json.dumps({'original_passed':6,'corrected_passed':20,'total':26,
    'compiled_binaries_unchanged':True,'binary_sha256':files},indent=2)+'\n')
POST
