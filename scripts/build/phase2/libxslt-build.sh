#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static --without-python \
 --without-crypto --without-plugins --docdir=/usr/share/doc/libxslt-1.1.45 > /build/configure.log 2>&1
make -j4
set +e
make check > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
make DESTDIR=/stage install > /build/stage.log 2>&1
python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');r={'scope':'Frozen libxslt1.1.45 xsltproc build SDK for owned GNOME Terminal UI XSLT generation, linked existing libxml2. Original make check retained. Optional deprecated Python/crypto/plugins disabled. Actual bounded CLI Unicode transform/malformed refusal/EXSLT write refusal-no-effect/two reset recovery cycles; selected flags are explicit, no blanket CLI parser sandbox or GUI/security closure claim. Native live image root must not acquire this build-only tool through Terminal runtime dependencies.','compile_exit':0,'stage_exit':0,'original_check_exit':int((p/'original-tests.exit').read_text()),'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
assert r['original_check_exit']==0;(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
