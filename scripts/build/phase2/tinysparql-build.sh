#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && ! -e /build/test-compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
[[ $(pkg-config --modversion sqlite3) == 3.53.4 ]]
mkdir -m700 /build/runtime
export XDG_RUNTIME_DIR=/build/runtime GSETTINGS_BACKEND=memory
common=(--prefix=/usr --libdir=lib --libexecdir=libexec --sysconfdir=/etc --wrap-mode=nofallback -Ddocs=false -Dman=false -Dintrospection=enabled -Dvapi=enabled -Dunicode_support=icu -Dstemmer=disabled -Davahi=disabled -Dbash_completion=false -Dbuiltin_modules=true -Doverride_sqlite_version_check=false)
meson setup /build/compile /src --buildtype=release -Ddebug=false -Dtests=false "${common[@]}"
ninja -C /build/compile -j4
meson install -C /build/compile --destdir /stage --no-rebuild
cc /src/toddy-probe.c -I/stage/usr/include/tinysparql-3.0 -L/stage/usr/lib \
 $(pkg-config --cflags --libs gio-2.0) -ltinysparql-3.0 -Wl,-rpath,/stage/usr/lib -o /build/native-probe
mkdir /build/consumer
/build/native-probe /build/consumer > /build/native-consumer.json
# A separate debug-enabled original test tree cannot replace production ELF proof.
meson setup /build/test-compile /src --buildtype=debugoptimized -Ddebug=true -Dtests=true "${common[@]}"
ninja -C /build/test-compile -j4
meson introspect /build/test-compile --tests > /build/original-registered-tests.json
# Frozen book requires a graphical session for the functional suite. Compile and
# retain it; CLI man-page test also unqualified with intentionally absent docs.
set +e
dbus-run-session -- meson test -C /build/test-compile --no-rebuild --print-errorlogs -j2 --no-suite functional > /build/original-tests.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /build/original-tests.exit
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(x) for x in (p/'test-compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()];assert rows
registered=json.loads((p/'original-registered-tests.json').read_text());pending=[r['name'] for r in registered if any(s.endswith(':functional') or s=='functional' for s in r.get('suite',[]))]
r={'scope':'Frozen Tinysparql3.11.1, existing SQLite3.53.4 unchanged and unsafe-version guard enabled. Production release debugfalse/testsfalse staged before separate debug-enabled test tree. ICU/GI/Vala/Soup3, builtin selected modules; optional docs/man/stemmer/Avahi/completion omitted. Selected original nonfunctional suites, functional/GUI-session+man-page scope compiled/deferred per frozen book. Known SQLite>=3.53.1 original sparql failure not a pass and must be reviewed before native qualification. Own real production local RDF Unicode/persistence/malformed-query refusal/reset only; no desktop/indexer/UI/permission/cancellation acceptance.','compile_exit':0,'stage_exit':0,'production_debug':False,'original_debug_test_tree':True,'original_tests_exit':int((p/'original-tests.exit').read_text()),'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'original_functional_tests_pending':pending,'consumer':json.loads((p/'native-consumer.json').read_text()),'artifacts':{str(f.relative_to(p/'compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'test_artifacts':{str(f.relative_to(p/'test-compile')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'test-compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
PY
[[ $result == 0 ]]
