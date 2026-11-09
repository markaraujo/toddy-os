#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/source ]]
export PYTHONDONTWRITEBYTECODE=1
cp -R /src /build/source
cd /build/source
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('make-ca');before=p.read_bytes();after=b'\n'.join(line.replace(b'-t ',b'') if b'mktemp' in line else line for line in before.split(b'\n'));assert after!=before;p.write_bytes(after)
Path('/build/book-correction.json').write_text(json.dumps({'reference':'Frozen BLFS13.1-systemd postlfs/make-ca.html remove obsolete mktemp -t, private worker copy only','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest()},indent=2)+'\n')
PY
make -j2 DESTDIR=/stage install
python3 /src/toddy-probe.py /stage > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');result={'scope':'make-ca1.16.1 tool stage/CLI only; real Mozilla data/default trust/provider/update/recovery pending','build_exit':0,'stage_exit':0,'upstream_tests':'No registered automated suite in source Makefile; actual data/provider tests are separate gates','book_correction':json.loads((p/'book-correction.json').read_text()),'consumer':json.loads((p/'native-consumer.json').read_text()),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
