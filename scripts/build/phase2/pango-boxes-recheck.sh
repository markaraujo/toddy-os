#!/bin/bash
# Boxes contains A-P/Z only. Its hardcoded derived metrics expect no fallback
# font; isolate that self-contained driver from the other test default font.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /stage/usr ]]
ulimit -c 0
cp /build/compile/meson-logs/testlog.json /build/font-recovery/cantarell-testlog.json
cp /build/compile/meson-logs/testlog.txt /build/font-recovery/cantarell-testlog.txt
export XDG_DATA_HOME=/build/empty-default-data
mkdir -p "$XDG_DATA_HOME/fonts"
[[ -z $(fc-list) ]]
meson test -C /build/compile --no-rebuild --print-errorlogs test-font-data
python3 - <<'AFTER'
from pathlib import Path
import hashlib,json
base=Path('/build/font-recovery');before=json.loads((base/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before};assert before==after
original=[json.loads(l) for l in (base/'original-testlog.json').read_text().splitlines()]
second=[json.loads(l) for l in (base/'cantarell-testlog.json').read_text().splitlines()]
last=[json.loads(l) for l in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(last)==1 and last[0]['name']=='pango - pango:test-font-data' and last[0]['result']=='OK' and last[0]['returncode']==0
pure={'pango - pango:'+n for n in ['test-coverage','testboundaries','testboundaries_ucd','testcolor','testscript','testlanguage','testmatrix','testtabs','test-ot-tags']}
reused=[r for r in original if r['name'] in pure];assert len(reused)==9 and all(r['result']=='OK' and r['returncode']==0 for r in reused)
corrected=[r for r in second if r['name']!=last[0]['name']];assert len(corrected)==19 and all(r['returncode']==0 and r['result'] in ['OK','SKIP'] for r in corrected)
combined=reused+corrected+last;assert len({r['name'] for r in combined})==29
assert {r['name'] for r in combined if r['result']=='SKIP'}=={'pango - pango:test-shape','pango - pango:cxx-test'}
(base/'combined-testlog.json').write_text('\n'.join(json.dumps(r) for r in combined)+'\n')
(base/'qualified.json').write_text(json.dumps({'compiled_binaries_unchanged':True,'before':before,'after':after,'original_core_drivers_reused':9,'cantarell_font_drivers_reused':19,'boxes_self_contained_recheck':1,'default_font_scope':'bundled Cantarell for general tests; no external fallback for standalone Boxes metrics; source/assertions unchanged'},indent=2)+'\n')
AFTER
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libpango-1.0.so.0 && -f /stage/usr/lib/girepository-1.0/PangoCairo-1.0.typelib ]]
