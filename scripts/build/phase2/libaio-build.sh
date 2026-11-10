#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && $(uname -m) == x86_64 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
cp -a /src /build/compile
cd /build/compile
test "$(sed -n '/install.*libaio[.]a/p' src/Makefile | wc -l)" = 1
sed -i '/install.*libaio[.]a/s/^/#/' src/Makefile
make -j4 > /build/original-build.log 2>&1

# Original case 14 writes 768 MiB. Run the unchanged suite inside the existing
# one-GiB private tmpfs and retain the real result before that mount disappears.
test "$(stat -f -c %T /tmp)" = tmpfs
test "$(df -B1 --output=avail /tmp | tail -1)" -ge 1000000000
cp -a /build/compile /tmp/libaio-partcheck
timeout 150 make -C /tmp/libaio-partcheck partcheck > /build/original-partcheck.log 2>&1
make DESTDIR=/stage install > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib -laio -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path
import re

work = Path('/build')
stage = Path('/stage')
log = (work / 'original-partcheck.log').read_text()
summary = re.search(r'Pass: (\d+)  Fail: (\d+)  Skip: (\d+)', log)
cases = re.findall(r'^Completed cases/(\d+)[.]p with (\d+).*$', log, re.MULTILINE)
assert summary and int(summary[2]) == 0 and len(cases) == 19
assert int(summary[1]) + int(summary[3]) == len(cases)
assert len({case for case, _ in cases}) == len(cases)
assert any(case == '14' and result == '0' for case, result in cases)
consumer = (work / 'local-probe.log').read_text()
assert consumer == 'Linux AIO invalid-depth refusal and two asynchronous file write/read recoveries passed\n'
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
assert artifacts and 'usr/include/libaio.h' in payload and not any(p.endswith('.a') for p in payload)
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'compile_exit': 0, 'stage_exit': 0, 'version': '0.3.113',
          'original_partcheck': {'passed': int(summary[1]), 'failed': int(summary[2]), 'skipped': int(summary[3]),
                                 'case_exit_status': cases, 'internal_skip_messages': [line for line in log.splitlines() if '[SKIP' in line]},
          'root_only_ext2_enospc_excluded_by_partcheck': ['8', '10'],
          'test_fixtures': 'Existing isolated 1 GiB tmpfs, including original case 14',
          'consumer': consumer, 'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
