#!/bin/bash
# Supported upstream Meson backend, preserving exact published Python metadata.
set -euo pipefail
[[ $(id -u) == 101 && -f /src/meson.build ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dpython=/usr/bin/python3 -Dtests=enabled -Ddoc=disabled -Dinstalled_tests=false
ninja -C /build/compile -j4
meson test -C /build/compile --no-rebuild --print-errorlogs -j2 > /build/original-tests.log 2>&1
printf '0\n' > /build/original-tests.exit
DESTDIR=/stage ninja -C /build/compile install
python3 - <<'PY'
from pathlib import Path
import email.parser,shutil,sysconfig
info=Path('/src/dbus_python.egg-info');data=email.parser.Parser().parsestr((info/'PKG-INFO').read_text())
assert data['Name']=='dbus-python' and data['Version']=='1.4.0'
site=Path('/stage')/Path(sysconfig.get_path('platlib')).relative_to('/')
assert site.is_dir();shutil.copytree(info,site/'dbus_python-1.4.0.egg-info')
PY
export PYTHONPATH=/stage/usr/lib/python3.14/site-packages
export PYTHONDONTWRITEBYTECODE=1
dbus-run-session -- python3 -B /src/toddy-probe.py > /build/native-consumer.json
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/build');rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());assert len(rows)==len(registered)==8
expected={'import-repeatedly','client','exception-py3','p2p','signals','standalone','unusable-main-loop','run-test.sh'}
assert {r['name'].split(':')[-1] for r in rows}==expected
for r in rows:
 if r['name'].split(':')[-1]=='import-repeatedly':
  assert r['result']=='SKIP' and r['returncode']==0 and r['stdout']=='1..1\nok 1 # SKIP https://gitlab.freedesktop.org/dbus/dbus-python/-/issues/55\n' and not r.get('stderr')
 else:assert r['result']=='OK' and r['returncode']==0
assert '#if DBUSPY_PY_VERSION_AT_LEAST(3, 12, 0, 0)' in Path('/src/test/import-repeatedly.c').read_text()
proof={'scope':'Native Python3.14 extension original eight private-bus driver programs and actual typed owner/error/name/reconnect; test dependency, not Polkit/GNOME acceptance','compile_exit':0,'stage_exit':0,'original_tests':[{k:r[k] for k in ['name','result','returncode']} for r in rows],'upstream_passed_programs':7,'upstream_skipped_programs':1,'unqualified':'Repeated embedded-interpreter reinitialization is explicitly skipped by upstream for Python>=3.12; not a pass. Selected test-tool profile uses one initialization per process.','native_consumer_exit':0,'consumer':json.loads((p/'native-consumer.json').read_text()),'stage_sha256':{str(f.relative_to(p/'stage')):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'stage').rglob('*') if f.is_file() and not f.is_symlink()}}
(p/'stage-results.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
