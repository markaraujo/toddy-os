#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback \
    -Dlibdbus=enabled -Djson-c=enabled -Dopenssl=enabled -Dkeyutils=enabled -Dpython=disabled \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --no-rebuild --print-errorlogs --num-processes 2 > /build/original-tests.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -isystem /stage/usr/include -L/stage/usr/lib \
    -Wl,-rpath-link,/stage/usr/lib -lnvme-mi -lnvme -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
python3 - <<'PYTEST'
from pathlib import Path
import hashlib
import json
import os

work = Path('/build')
stage = Path('/stage')
tests = json.loads((work / 'original-registered-tests.json').read_text())
results = [json.loads(line) for line in (work / 'compile/meson-logs/testlog.json').read_text().splitlines()]
registered = {row['name'] for row in tests}
for row in results:
    assert row['name'].startswith('libnvme:')
    row['name'] = row['name'].removeprefix('libnvme:')
assert len(registered) == len(tests) == len(results) == 38
assert registered == {row['name'] for row in results}
expected_failures = {'NBFT-bad-oldspec', 'NBFT-random-noise'}
assert all(row['result'] == ('EXPECTEDFAIL' if row['name'] in expected_failures else 'OK') for row in results)
consumer = (work / 'local-probe.log').read_text()
assert consumer == 'NVMe UUID refusal and roundtrip with two fresh local MI contexts passed\n'
options = {row['name']: row['value'] for row in json.loads((work / 'compile/meson-info/intro-buildoptions.json').read_text())}
for name in ('json-c', 'openssl', 'keyutils', 'libdbus'):
    assert options[name] == 'enabled'
assert options['python'] == options['liburing'] == 'disabled'
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*')
             if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
assert artifacts and {'usr/include/libnvme.h', 'usr/include/libnvme-mi.h',
                      'usr/lib/pkgconfig/libnvme.pc', 'usr/lib/pkgconfig/libnvme-mi.pc'} <= payload.keys()
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '1.16.2', 'compile_exit': 0, 'stage_exit': 0,
          'tests': [{'name': row['name'], 'result': row['result']} for row in results],
          'original_hardware_programs_deferred': ['main-test', 'test-register', 'test-zns'],
          'consumer': consumer, 'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
