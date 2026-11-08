#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && -d /build/compile && ! -e /build/consumer && ! -e /build/test-results.json ]]
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build/libpciaccess-stage-before.json');assert not p.exists()
files={str(f.relative_to('/stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/stage').rglob('*') if f.is_file() and not f.is_symlink()}
assert files;p.write_text(json.dumps(files,indent=2)+'\n')
PY
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib \
    $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs pciaccess) -o /build/consumer
LD_LIBRARY_PATH=/stage/usr/lib /build/consumer
python3 - <<'PY'
from pathlib import Path
import hashlib,json
before=json.loads(Path('/build/libpciaccess-stage-before.json').read_text())
after={str(f.relative_to('/stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/stage').rglob('*') if f.is_file() and not f.is_symlink()}
assert after==before
Path('/build/test-results.json').write_text(json.dumps({'registered_upstream_tests':0,'upstream_suite':'Not provided by source Meson recipe; empty target is not test acceptance','staged_consumer_exit':0,'stage_regular_files_unchanged':len(before),'recovery':'Original1 compiled/staged; only C fixture extension corrected, consumer-only resume2; no rebuild','scope':'Native unknown-ID API and cleanup only, no hardware enumeration/device write'},indent=2)+'\n')
PY
