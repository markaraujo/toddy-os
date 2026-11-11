#!/bin/bash
# Two unmodified upstream consumers linked against the actual installed library.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/native-probes.json ]]
[[ ! -e /build/native-hello && ! -e /build/native-test-signals ]]
cc -O2 /src/example/hello.c $(pkg-config --cflags --libs fuse3) -o /build/native-hello
cc -O2 /src/test/test_signals.c -I/build/compile -I/src/lib $(pkg-config --cflags --libs fuse3) -o /build/native-test-signals
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
w=Path('/build');rows={}
for name in ['native-hello','native-test-signals']:
 p=w/name;dynamic=subprocess.check_output(['readelf','-d',str(p)],text=True)
 assert 'libfuse3.so.4' in dynamic and '(RPATH)' not in dynamic and '(RUNPATH)' not in dynamic
 assert not p.stat().st_mode&0o6000
 rows[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'no_rpath':True}
library=Path('/usr/lib/libfuse3.so.4').resolve();assert library.is_relative_to('/usr/lib')
r={'scope':'Unmodified upstream example/hello.c and test/test_signals.c compiled as ordinary UID101/NNP test drivers against actual installed libfuse3.so.4, no RPATH or privilege. Not an executed mount/signals test.','consumers':rows,'library':str(library),'library_sha256':hashlib.sha256(library.read_bytes()).hexdigest(),'source_sha256':{n:hashlib.sha256((Path('/src')/n).read_bytes()).hexdigest() for n in ['example/hello.c','test/test_signals.c']}}
(w/'native-probes.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
PY
