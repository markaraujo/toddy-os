#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
pkg-config --modversion libudev > /build/libudev-version.log
/src/configure --prefix=/usr --disable-static > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make DESTDIR=/stage docdir=/usr/share/doc/libatasmart-0.19 install > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror -include stddef.h /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -latasmart -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe /src/blob-examples/ST9160821AS--3.CLH \
    /src/blob-examples/WDC_WD5000AAKS--00TMA0-12.01C01 > /build/local-probe.log
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path

work = Path('/build')
stage = Path('/stage')
expected = 'Two upstream SMART blobs parsed, truncation refused, ATA model retained and valid reload passed\n'
consumer = (work / 'local-probe.log').read_text()
assert consumer == expected
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*')
             if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
assert artifacts and {'usr/include/atasmart.h', 'usr/lib/pkgconfig/libatasmart.pc',
                      'usr/sbin/skdump', 'usr/sbin/sktest'} <= payload.keys()
assert not any(p.endswith('.a') for p in payload)
free = os.statvfs(work)
assert free.f_bavail * free.f_frsize >= 16 * 1024**3
result = {'compile_exit': 0, 'stage_exit': 0, 'version': '0.19',
          'original_suite_supplied': False, 'consumer': consumer,
          'fixture_scope': 'Upstream bundled blobs only. No block devices or SMART commands.',
          'libudev_version': (work / 'libudev-version.log').read_text().strip(),
          'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
