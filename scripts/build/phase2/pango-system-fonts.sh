#!/bin/bash
# Only font-sensitive drivers whose system-font inputs changed after Adwaita.
set -euo pipefail
[[ $(id -u) == 101 && -d /build/compile && ! -e /build/system-fonts ]]
ulimit -c 0
export XDG_DATA_HOME=/build/test-default-data
mkdir /build/system-fonts
python3 - <<'BEFORE'
import hashlib,json,subprocess
from pathlib import Path
before=json.loads(Path('/build/font-recovery/before.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in before.items())
fonts=list(Path('/usr/share/fonts/Adwaita').glob('*.ttf'));assert len(fonts)==6
inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fonts)}
cantarell=Path('/src/tests/fonts/Cantarell-VF.otf');inputs[str(cantarell)]=hashlib.sha256(cantarell.read_bytes()).hexdigest()
resolved={f:subprocess.check_output(['fc-match','-f','%{family}|%{file}\n',f],text=True).strip() for f in ['serif','sans-serif','monospace']}
Path('/build/system-fonts/inputs.json').write_text(json.dumps({'font_sha256':inputs,'effective_defaults':resolved,'compiled_binaries':before},indent=2)+'\n')
BEFORE
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 4 \
    --logbase system-fonts-testlog \
    test-bidi testcontext testiter test-ellipsize markup-parse test-itemize \
    test-font testattributes test-harfbuzz test-break testmisc testserialize \
    test-layout test-layout2 test-fonts test-no-fonts test-pangocairo-threads
python3 - <<'AFTER'
import hashlib,json
from pathlib import Path
directory=Path('/build/system-fonts');proof=json.loads((directory/'inputs.json').read_text())
for field in ['font_sha256','compiled_binaries']:
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in proof[field].items())
log=Path('/build/compile/meson-logs/system-fonts-testlog.json')
rows=[json.loads(line) for line in log.read_text().splitlines()]
assert len(rows)==17 and len({r['name'] for r in rows})==17
assert all(r['result']=='OK' and r['returncode']==0 for r in rows)
proof.update({'affected_drivers_passed':17,'raw_testlog_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
              'compiled_binaries_unchanged':True,
              'scope':'Changed system font inputs only; nine core passes and independent full-ASCII metric oracle reused, original golden failure retained. No rebuild/reinstall or graphical acceptance'})
(directory/'qualified.json').write_text(json.dumps(proof,indent=2)+'\n')
AFTER
