#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --sysconfdir=/etc --disable-static --enable-gssapi > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
make DESTDIR=/stage install > /build/original-stage.log 2>&1
cc -Wall -Wextra -Werror /src/toddy-probe.c -I/stage/usr/include/tirpc -L/stage/usr/lib \
    -Wl,-rpath-link,/stage/usr/lib -ltirpc -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
readelf -d /stage/usr/lib/libtirpc.so.3 > /build/stage-shared-links.log
python3 - <<'PYTEST'
import hashlib
import json
import os
from pathlib import Path

work = Path('/build')
stage = Path('/stage')
consumer = (work / 'local-probe.log').read_text()
assert consumer == 'TI-RPC XDR byte order, truncation refusal and two local recoveries passed\n'
assert 'libgssapi_krb5.so.2' in (work / 'stage-shared-links.log').read_text()
artifacts = {str(p.relative_to(work / 'compile')): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (work / 'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
payload = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in stage.rglob('*') if p.is_file() and not p.is_symlink()}
required = {'usr/include/tirpc/rpc/xdr.h', 'usr/lib/pkgconfig/libtirpc.pc', 'etc/netconfig'}
assert artifacts and required <= payload.keys() and not any(p.endswith('.a') for p in payload)
space = os.statvfs(work)
assert space.f_bavail * space.f_frsize >= 16 * 1024**3
result = {'version': '1.3.7', 'compile_exit': 0, 'stage_exit': 0, 'original_suite_supplied': False,
          'consumer': consumer, 'gssapi_linkage': True, 'artifacts': artifacts, 'stage_sha256': payload}
(work / 'stage-results.json').write_text(json.dumps(result, indent=2) + '\n')
PYTEST
