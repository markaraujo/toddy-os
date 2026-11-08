#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
meson setup /build/compile /src --prefix=/usr --buildtype=release --wrap-mode=nofallback
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4
python3 - <<'PY'
from pathlib import Path
import json,subprocess
domains=['iso_15924','iso_3166-1','iso_3166-2','iso_3166-3','iso_4217','iso_639-2','iso_639-3','iso_639-5']
results=[]
for domain in domains:
    files=list((Path('/src')/domain).glob('*.po'));assert files
    # Upstream Meson supplies a bare domain to a glob(prefix+'*po') checker.
    # Run that unchanged checker against its actual source directory, including
    # the separator, and assert a nonempty file set before accepting its exit.
    with Path('/build/utf8-'+domain+'.log').open('xb') as log:
        r=subprocess.run(['python3','/src/scripts/check_valid_utf8.py',domain+'/'],cwd='/src',stdout=log,stderr=subprocess.STDOUT)
    Path('/build/utf8-'+domain+'.exit').write_text(str(r.returncode)+'\n');assert r.returncode==0
    results.append({'domain':domain,'actual_po_files':len(files),'native_exit':r.returncode})
Path('/build/source-utf8-tests.json').write_text(json.dumps(results,indent=2)+'\n')
PY
DESTDIR=/stage ninja -C /build/compile install
python3 /src/toddy-probe.py /stage > /build/native-data.json
python3 - <<'PY'
from pathlib import Path
import json
rows=[json.loads(line) for line in Path('/build/compile/meson-logs/testlog.json').read_text().splitlines()]
assert len(rows)==8 and all(r['result']=='OK' and r['returncode']==0 for r in rows)
Path('/build/test-results.json').write_text(json.dumps({'scope':'Native ISO data/gettext APIs and actual source-file UTF8 checks; no window/session acceptance',
    'registered_drivers':8,'registered_driver_note':'Bare-domain checker glob can be empty; not used alone as UTF8 evidence',
    'actual_source_utf8':json.loads(Path('/build/source-utf8-tests.json').read_text()),
    'staged_consumer_exit':0,'consumer':json.loads(Path('/build/native-data.json').read_text())},indent=2)+'\n')
PY
