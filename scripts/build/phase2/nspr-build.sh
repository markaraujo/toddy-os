#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
mkdir /build/compile
cd /build/compile
/src/nspr/configure --prefix=/usr --libdir=/usr/lib --with-mozilla --with-pthreads --enable-64bit --enable-optimize --disable-debug
make -j4
# The frozen book does not recommend its full combined development suite for a
# released optimized NSPR. Select actual independent runtime originals instead.
make -C pr/tests -j2 atomic prftest vercheck
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess
p=Path('/build');env={**os.environ,'LD_LIBRARY_PATH':'/build/compile/dist/lib'};rows=[]
for name in ['atomic','prftest','vercheck']:
 with (p/('original-'+name+'.log')).open('x') as log:r=subprocess.run([str(p/'compile/pr/tests'/name)],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=30)
 rows.append({'name':name,'exit':r.returncode});assert r.returncode==0
(p/'original-results.json').write_text(json.dumps(rows,indent=2)+'\n')
PY
make DESTDIR=/stage install
cc /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lnspr4 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
/build/native-probe /build/private-native-file > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');assert not (p/'private-native-file').exists()
result={'scope':'Three selected original runtime programs and actual threads/locks/private-file/version/refusal/recovery; not full combined NSPR/NSS development suite/network/TLS','compile_exit':0,'stage_exit':0,'original_tests':json.loads((p/'original-results.json').read_text()),'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
