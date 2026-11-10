#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Dtests=true -Ddistro_install=true -Dwith_INIReader=true
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --no-rebuild --print-errorlogs -j4 > /build/original-tests.log 2>&1
printf '0\n' > /build/original-tests.exit
meson install -C /build/compile --no-rebuild --destdir /stage
c++ -x c++ -std=c++17 -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lINIReader -linih -o /build/native-probe
mkdir /build/consumer
/build/native-probe /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
w=Path('/build');rows=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==16 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
r={'scope':'Frozen inih62 C+INIReader C++ shared libraries/default bounded stack parser; all16original Meson programs and own C/C++ UTF8/typed-default/refusal/state-retention/recovery. No Exiv2/user-owned config or GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((w/'native-consumer.json').read_text()),'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('artifacts','stage_sha256')}))
PY
