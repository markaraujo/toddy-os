#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dsnap=false -Ddocumentation=false -Dmalcontent=false \
    -Dprivileged_group=wheel -Dtests=true > /build/configure.log 2>&1
ninja -C /build/compile -j6 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-test-inventory.json
python3 - <<'PYTEST'
from pathlib import Path
import hashlib
import json
import os

work = Path('/build')
compile_dir = work / 'compile'
artifacts = {}
for path in compile_dir.rglob('*'):
    if path.is_file() and not path.is_symlink():
        with path.open('rb') as stream:
            if stream.read(4) != b'\x7fELF':
                continue
            stream.seek(0)
            artifacts[str(path.relative_to(compile_dir))] = hashlib.file_digest(stream, 'sha256').hexdigest()
assert 'shell/gnome-control-center' in artifacts
assert artifacts
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 128 * 1024**2
result = {'version':'50.4', 'compile_exit':0, 'artifacts':artifacts,
          'registered_test_count':len(json.loads((work/'original-test-inventory.json').read_text())),
          'scope':'Isolated compiler output and registered upstream test inventory. No tests, staging, native install or GUI acceptance yet.'}
(work/'compile-results.json').write_text(json.dumps(result, indent=2)+'\n')
PYTEST
