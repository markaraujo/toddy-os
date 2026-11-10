#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --disable-ssh-token --disable-asciidoc > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1

# These upstream targets operate on vectors, CLI arguments or library symbols.
# Device, keyring and kernel integration suites need a disposable native guest.
make -C tests -j4 test-symbols-list.h vectors-test unit-utils-crypt-test all-symbols-test > /build/original-test-build.log 2>&1
(
    cd tests
    unset CRYPTSETUP_PATH
    timeout 120 ./vectors-test > /build/original-vectors.log 2>&1
    timeout 30 ./unit-utils-crypt-test > /build/original-unit-utils-crypt.log 2>&1
    timeout 30 /src/tests/run-all-symbols > /build/original-symbols.log 2>&1
    timeout 60 /src/tests/compat-args-test > /build/original-compat-args.log 2>&1
)
make DESTDIR=/stage install > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include -L/stage/usr/lib \
    -Wl,-rpath-link,/stage/usr/lib -lcryptsetup -o /build/local-probe
mkdir /tmp/toddy-cryptsetup
xz -dc /src/tests/luks2_valid_hdr.img.xz > /tmp/toddy-cryptsetup/valid.img
truncate -s 16M /tmp/toddy-cryptsetup/bad.img
chmod 0400 /tmp/toddy-cryptsetup/{valid,bad}.img
sha256sum /tmp/toddy-cryptsetup/{valid,bad}.img > /build/fixture-before.sha256
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe /tmp/toddy-cryptsetup/{valid,bad}.img > /build/local-probe.log 2>&1
sha256sum -c /build/fixture-before.sha256 > /build/fixture-retained.log
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path
import re

work = Path('/build')
stage = Path('/stage')
symbols = re.search(r'Performed (\d+) symbol checks in total[.]', (work / 'original-symbols.log').read_text())
assert symbols and int(symbols[1]) > 0
vectors = (work / 'original-vectors.log').read_text()
assert 'crypto backend.' in vectors and '[FAILED]' not in vectors
consumer = (work / 'local-probe.log').read_text()
assert 'Cryptsetup LUKS2 metadata refusal and two header reloads passed\n' in consumer
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
required = {'usr/include/libcryptsetup.h', 'usr/lib/pkgconfig/libcryptsetup.pc', 'usr/sbin/cryptsetup'}
assert artifacts and required <= payload.keys()
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '2.8.7', 'compile_exit': 0, 'stage_exit': 0,
          'original_selected_programs': ['vectors-test', 'unit-utils-crypt-test', 'run-all-symbols', 'compat-args-test'],
          'symbol_checks': int(symbols[1]), 'vector_unavailable': [line for line in vectors.splitlines() if '[N/A]' in line],
          'consumer': consumer, 'fixture_bytes_unchanged': True, 'artifacts': artifacts, 'stage_sha256': payload,
          'device_and_kernel_suites_pending': True}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
