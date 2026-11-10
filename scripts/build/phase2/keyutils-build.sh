#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
cp -a /src /build/compile
cd /build/compile
make -j4 > /build/original-build.log 2>&1
make DESTDIR=/stage NO_ARLIB=1 LIBDIR=/usr/lib BINDIR=/usr/bin SBINDIR=/usr/sbin install > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/build/compile -lkeyutils -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/bin/keyctl --version > /build/keyctl-version.log
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path
import re

work = Path('/build')
stage = Path('/stage')
consumer = (work / 'local-probe.log').read_text()
version = (work / 'keyctl-version.log').read_text()
assert consumer == 'Keyutils C shared version and build metadata verified\n'
assert re.fullmatch(r'keyctl from keyutils-1[.]6[.]3 \(Built [0-9]{4}-[0-9]{2}-[0-9]{2}\)\n', version)
assert (work / 'compile/cxx.stamp').is_file()
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
required = {
    'usr/include/keyutils.h',
    'usr/lib/pkgconfig/libkeyutils.pc',
    'usr/bin/keyctl',
    'usr/sbin/request-key',
    'usr/sbin/key.dns_resolver',
    'etc/request-key.conf',
}
assert artifacts and required <= payload.keys()
assert not any(p.endswith('.a') for p in payload)
assert payload['etc/request-key.conf'] == hashlib.sha256(Path('/src/request-key.conf').read_bytes()).hexdigest()
free = os.statvfs(work)
assert free.f_bavail * free.f_frsize >= 16 * 1024**3
result = {'compile_exit': 0, 'stage_exit': 0, 'version': '1.6.3',
          'CXX_header_syntax': True, 'consumer': consumer, 'CLI': version,
          'original_suite_pending': 'Frozen BLFS requires installed package and a native non-chroot kernel context.',
          'scope': 'Local shared-library and CLI version checks. No keyring mutation, key handler or DNS invocation.',
          'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
