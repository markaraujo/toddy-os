#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --sysconfdir=/etc > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make DESTDIR=/stage install > /build/original-stage.log 2>&1

mkdir /build/probe
cd /build/probe
cat > fixture.x <<'FIXTURE'
struct fixture {
    unsigned int sequence;
    string label<12>;
};
FIXTURE
printf '%s\n' 'struct fixture { @ };' > invalid.x
/stage/usr/bin/rpcgen -C -h -o fixture.h fixture.x
/stage/usr/bin/rpcgen -C -c -o fixture_xdr.c fixture.x
set +e
/stage/usr/bin/rpcgen -C -h -o invalid.h invalid.x > /build/invalid-rpcgen.log 2>&1
invalid_status=$?
set -e
test "$invalid_status" -ne 0
test -s /build/invalid-rpcgen.log
mkdir recovery
/stage/usr/bin/rpcgen -C -h -o recovery/fixture.h fixture.x
cmp fixture.h recovery/fixture.h
cc -Wall -Wextra -Werror -I. $(pkg-config --cflags libtirpc) -c /src/toddy-probe.c -o consumer.o
cc -Werror=implicit-function-declaration $(pkg-config --cflags libtirpc) \
    fixture_xdr.c consumer.o $(pkg-config --libs libtirpc) -o consumer
./consumer > /build/local-probe.log
python3 - "$invalid_status" <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path
import sys

work = Path('/build')
stage = Path('/stage')
consumer = (work / 'local-probe.log').read_text()
assert consumer == 'Generated rpcgen XDR C round-tripped two records\n'
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
assert 'usr/bin/rpcgen' in payload and 'usr/include/rpcsvc/nfs_prot.h' in payload
assert artifacts
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '1.4.4', 'compile_exit': 0, 'stage_exit': 0, 'original_suite_supplied': False,
          'consumer': consumer, 'invalid_source_exit': int(sys.argv[1]),
          'generated_header_recovery_identical': True, 'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
