#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
    --disable-static --enable-available-modules --enable-introspection --disable-man > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
timeout 120 make -j4 check > /build/original-check.log 2>&1
make DESTDIR=/stage install > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/udisks2 -L/stage/usr/lib \
    $(pkg-config --cflags --libs gio-2.0) -ludisks2 -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0 LD_LIBRARY_PATH=/stage/usr/lib python3 - <<'GIPROBE' > /build/local-gi.log
import gi
gi.require_version('UDisks', '2.0')
from gi.repository import UDisks
assert gi.Repository.get_default().get_typelib_path('UDisks') == '/stage/usr/lib/girepository-1.0/UDisks-2.0.typelib'
for cycle in range(2):
    m = UDisks.ManagerSkeleton.new()
    m.props.version = '2.11.2'
    assert m.props.version == '2.11.2'
print('UDisks 2 GI metadata and two local manager objects passed')
GIPROBE
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path
import re

work = Path('/build')
stage = Path('/stage')
test = (work / 'compile/src/tests/udisks-test.log').read_text()
cases = re.findall(r'^ok \d+ (/udisks/daemon/\S+)', test, re.MULTILINE)
assert len(cases) == len(set(cases)) == 23 and '# SKIP' not in test
assert 'not ok ' not in test
consumer = (work / 'local-probe.log').read_text()
gi = (work / 'local-gi.log').read_text()
assert consumer == 'UDisks local D-Bus skeleton properties and two object lifecycles passed\n'
assert gi == 'UDisks 2 GI metadata and two local manager objects passed\n'
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
required = {'usr/lib/pkgconfig/udisks2.pc', 'usr/lib/girepository-1.0/UDisks-2.0.typelib',
            'usr/share/gir-1.0/UDisks-2.0.gir', 'usr/libexec/udisks2/udisksd', 'usr/bin/udisksctl'}
assert artifacts and required <= payload.keys()
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '2.11.2', 'compile_exit': 0, 'stage_exit': 0, 'original_cases': cases,
          'consumer': consumer, 'gi_consumer': gi, 'artifacts': artifacts, 'stage_sha256': payload,
          'daemon_activation_and_device_tests_pending': True}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
