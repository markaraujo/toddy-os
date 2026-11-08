#!/bin/bash
# Correct fixture font discovery only; never patch compiled code or metric values.
set -euo pipefail
[[ $(id -u) == 101 && -d /build/compile && ! -e /stage/usr ]]
ulimit -c 0
mkdir /build/font-recovery
cp /build/compile/meson-logs/testlog.json /build/font-recovery/original-testlog.json
cp /build/compile/meson-logs/testlog.txt /build/font-recovery/original-testlog.txt
export XDG_DATA_HOME=/build/test-default-data
mkdir -p "$XDG_DATA_HOME/fonts"
ln -s /src/tests/fonts/Cantarell-VF.otf "$XDG_DATA_HOME/fonts/Cantarell-VF.otf"
[[ $(fc-match --format '%{family}' serif) == Cantarell ]]
python3 - <<'BEFORE'
from pathlib import Path
import json,hashlib
rows=[json.loads(l) for l in Path('/build/font-recovery/original-testlog.json').read_text().splitlines()]
files={r['command'][0] for r in rows}
files.update(str(p) for p in Path('/build/compile/pango').glob('lib*.so.*') if p.is_file() and not p.is_symlink())
Path('/build/font-recovery/before.json').write_text(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(files)},indent=2)+'\n')
BEFORE
# Nine non-font core drivers passed with identical binaries and unchanged inputs.
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4 \
    test-font-data test-bidi testcontext testiter test-ellipsize markup-parse \
    test-itemize test-shape test-font testattributes cxx-test test-harfbuzz \
    test-break testmisc testserialize test-layout test-layout2 test-fonts \
    test-no-fonts test-pangocairo-threads
python3 - <<'AFTER'
from pathlib import Path
import hashlib,json
base=Path('/build/font-recovery');before=json.loads((base/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};assert before==after
old=[json.loads(l) for l in (base/'original-testlog.json').read_text().splitlines()]
new=[json.loads(l) for l in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
unaffected={'pango - pango:'+n for n in ['test-coverage','testboundaries','testboundaries_ucd','testcolor','testscript','testlanguage','testmatrix','testtabs','test-ot-tags']}
assert len(old)==29 and len(new)==20
reused=[r for r in old if r['name'] in unaffected];assert len(reused)==9 and all(r['result']=='OK' and r['returncode']==0 for r in reused)
assert all(r['returncode']==0 and r['result'] in ['OK','SKIP'] for r in new)
combined=reused+new;assert len({r['name'] for r in combined})==29
(base/'combined-testlog.json').write_text('\n'.join(json.dumps(r) for r in combined)+'\n')
(base/'qualified.json').write_text(json.dumps({'compiled_binaries_unchanged':True,'before':before,'after':after,'reused_core_drivers':9,'corrected_font_drivers':20,'private_default_font':'unmodified bundled Cantarell-VF.otf, no global/expected-value changes'},indent=2)+'\n')
AFTER
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libpango-1.0.so.0 && -f /stage/usr/lib/girepository-1.0/PangoCairo-1.0.typelib ]]
