#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --libexecdir=libexec \
 --sysconfdir=/etc --buildtype=release --wrap-mode=nofallback \
 -Ddbg=false -Ddocs=false -Dnautilus_extension=false -Dsearch_provider=true
ninja -C /build/compile -j4
meson introspect /build/compile --tests > /build/original-registered-tests.json
set +e
meson test -C /build/compile --print-errorlogs -j2 > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
[[ $result == 0 ]]
meson install -C /build/compile --destdir /stage --no-rebuild
if [[ -f /src/toddy-schema-paths.patch ]]; then
 install -Dm644 /src/toddy-schema-paths.patch /stage/usr/share/doc/gnome-terminal/external-schema-paths.patch
fi
python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(x) for x in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert len(rows)==1 and rows[0]['result']=='OK' and rows[0]['returncode']==0
r={'scope':'Frozen GNOME Terminal3.60.0 GTK3/VTE2.91/libhandy with Shell search provider. Optional Nautilus extension/docs/debug omitted; frozen-book external proxy paths corrected, no network fallback. Original regex tests plus actual client version/invalid CLI refusal/private DConf profile Unicode/navy settings/invalid boolean refusal/persistence across two new buses/reset/system font preserved. No installed package/native widget/launch/focus/PTY/user-login acceptance. Shared stock schema cache union remains separate.','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
