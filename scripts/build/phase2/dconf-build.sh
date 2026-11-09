#!/bin/bash
# Original core/runtime tests; the optional graphical editor is a separate package.
set -euo pipefail
[[ $(id -u) == 101 ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc \
    --buildtype=release --wrap-mode=nodownload -Dgvdb:tests=true -Dman=false -Dgtk_doc=false -Dvapi=false -Dbash_completion=false
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --no-suite lint --print-errorlogs -j1 > /build/original-tests.log 2>&1
DESTDIR=/stage ninja -C /build/compile install
python3 /src/toddy-probe.py /stage /build/consumer > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(line) for line in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if line.strip()]
assert len(rows)==16 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text())
assert len([r for r in registered if 'dconf:lint' not in r['suite']])==16
result={'scope':'Original DConf core/runtime/ABI tests and actual private-bus typed persistence/error/reconnect/reset; no full GNOME settings acceptance','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'excluded':'Optional shellcheck lint suite, not a runtime pass; graphical DConf Editor not selected','consumer':json.loads((p/'native-consumer.json').read_text()),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(result,indent=2)+'\n')
PY
