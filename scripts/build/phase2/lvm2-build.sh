#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
export PATH="$PATH:/usr/sbin"
ulimit -c 0
cp -a /src /build/compile
cd /build/compile
./configure --prefix=/usr --enable-cmdlib --enable-pkgconfig --enable-udev_sync > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make -j4 unit-test > /build/original-unit-build.log 2>&1
# Execute the upstream binary directly. The make wrapper's final rm can hide
# the test process status. Keep bounded temporary test files on private tmpfs.
mkdir /tmp/lvm2-unit
(
    cd /tmp/lvm2-unit
    export LD_LIBRARY_PATH=/build/compile/libdm:/build/compile/daemons/dmeventd
    /build/compile/test/unit/unit-test list > /build/original-unit-list.log 2>&1
    timeout 150 /build/compile/test/unit/unit-test run > /build/original-unit-run.log 2>&1
)
make DESTDIR=/stage install > /build/original-stage.log 2>&1
make DESTDIR=/stage install_systemd_units > /build/original-stage-systemd.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -ldevmapper -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe
printf '%s\n' 'Device Mapper name escapes and two local pool lifecycles passed' > /build/local-probe.log
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path
import re

work = Path('/build')
stage = Path('/stage')
run = (work / 'original-unit-run.log').read_text()
summary = re.search(r'^(\d+)/(\d+) tests passed$', run, re.MULTILINE)
assert summary and int(summary[1]) == int(summary[2]) > 0
cases = re.findall(r'^\[RUN    \] (.+)$', run, re.MULTILINE)
assert len(cases) == len(set(cases)) == int(summary[2])
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
required = {'usr/include/libdevmapper.h', 'usr/lib/pkgconfig/devmapper.pc',
            'usr/sbin/lvm', 'usr/sbin/dmsetup', 'etc/lvm/lvm.conf'}
assert artifacts and required <= payload.keys()
assert any(path.startswith('usr/lib/udev/rules.d/') for path in payload)
assert any(path.startswith('usr/lib/systemd/system/') for path in payload)
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'compile_exit': 0, 'stage_exit': 0, 'version': '2.03.42',
          'unit_cases_passed': cases, 'consumer': (work / 'local-probe.log').read_text(),
          'original_device_tests_pending': True, 'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
