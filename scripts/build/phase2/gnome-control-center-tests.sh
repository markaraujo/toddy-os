#!/bin/bash
set -euo pipefail
test "$(id -u)" = 101
export GTK_A11Y=none PYTHONDONTWRITEBYTECODE=1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/original-tests.log 2>&1
python3 - <<'PYTEST'
from pathlib import Path
import hashlib
import json
work=Path('/build')
original=json.loads((work/'compile-results.json').read_text())
rows=[json.loads(line) for line in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if line.strip()]
assert len(rows)==4
expected={'validate-metainfo','test-hostname','test-wif-panel-text','test-shift'}
assert {r['name'].removeprefix('gnome-control-center:') for r in rows}==expected
assert all(row['returncode']==0 and row['result']=='OK' for row in rows)
for relative,sha in original['artifacts'].items():
    path=work/'compile'/relative
    with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==sha
summary=[{'name':r['name'],'returncode':r['returncode'],'result':r['result'],
          'stdout':r.get('stdout',''),'stderr':r.get('stderr','')} for r in rows]
(work/'portable-tests-results.json').write_text(json.dumps({'rows':summary,'unchanged_elf_count':len(original['artifacts']),
    'scope':'Four registered original portable test programs. Graphical network tests were not registered without Xvfb; no graphical acceptance.'},indent=2)+'\n')
PYTEST
