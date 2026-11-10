#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
cp -a /src /build/compile
cd /build/compile
./configure --prefix=/usr --disable-static > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make check > /build/original-check.log 2>&1
# The upstream test script reports individual failures without returning them.
python3 - <<'PYTEST'
from pathlib import Path
import re
s = Path('/build/compile/tests/testit.sh.log').read_text()
assert not re.search(r'^FAIL(?:[: ]|$)', s, re.MULTILINE)
assert len(set(re.findall(r'^PASS:? (test1 - \d+|test3 - \d+)$', s, re.MULTILINE))) == 65
PYTEST
make DESTDIR=/stage install > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -lpopt -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path

work = Path('/build')
stage = Path('/stage')
consumer = (work / 'local-probe.log').read_text()
assert consumer == 'Popt unknown option refusal and two typed argument recoveries passed\n'
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
assert artifacts and {'usr/include/popt.h', 'usr/lib/pkgconfig/popt.pc'} <= payload.keys()
assert not any(p.endswith('.a') for p in payload)
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '1.19', 'compile_exit': 0, 'stage_exit': 0,
          'upstream_nested_cases_passed': 65, 'consumer': consumer,
          'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
