#!/bin/bash
# ADR0122: preserve failed upstream golden, require independent native oracle.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /stage/usr ]]
python3 - <<'PY'
import hashlib,json
from pathlib import Path
work=Path('/build');base=work/'font-recovery'
proof=json.loads((work/'metric-oracle/qualified.json').read_text())
assert proof['portable_cases_passed']==3 and proof['test_exit']==0
assert proof['derived_font_sha256']=='4a9a161f3afb5e7897bff0f4f1341686d8536b8630e9edd22d60118ccc2c92d2'
assert hashlib.sha256((work/'metric-oracle/test.log').read_bytes()).hexdigest()==proof['test_log_sha256']
before=proof['original_binary_sha256'];after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in before}
assert before==after and before==json.loads((base/'before.json').read_text())
def rows(name):return [json.loads(l) for l in (base/name).read_text().splitlines()]
original=rows('original-testlog.json');curated=rows('cantarell-testlog.json')
unaffected={'pango - pango:'+n for n in ['test-coverage','testboundaries','testboundaries_ucd','testcolor','testscript','testlanguage','testmatrix','testtabs','test-ot-tags']}
reused=[r for r in original if r['name'] in unaffected]
assert len(original)==29 and len(curated)==20 and len(reused)==9
assert all(r['result']=='OK' and r['returncode']==0 for r in reused)
failed=[r for r in curated if r['result'] not in ('OK','SKIP')]
assert len(failed)==1 and failed[0]['name']=='pango - pango:test-font-data' and failed[0]['returncode']!=0
accepted=[r for r in curated if r not in failed]
assert len(accepted)==19 and all(r['returncode']==0 for r in accepted)
assert {r['name'] for r in accepted if r['result']=='SKIP'}=={'pango - pango:cxx-test','pango - pango:test-shape'}
assert len({r['name'] for r in reused+curated})==29
result={'scope':'9 original core passes,17 curated font driver passes,2 empty upstream drivers,3 separately adapted metric cases; original golden remains failed',
        'original_binaries_unchanged':True,'binaries':after,'core_passed':9,'curated_passed':17,'empty_drivers':2,'portable_metric_cases_passed':3,
        'proofs':{str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [base/'original-testlog.json',base/'cantarell-testlog.json',work/'metric-oracle/qualified.json']}}
(work/'portable-qualified.json').write_text(json.dumps(result,indent=2)+'\n')
PY
DESTDIR=/stage ninja -C /build/compile install
[[ -f /stage/usr/lib/libpango-1.0.so.0 && -f /stage/usr/lib/girepository-1.0/PangoCairo-1.0.typelib ]]
