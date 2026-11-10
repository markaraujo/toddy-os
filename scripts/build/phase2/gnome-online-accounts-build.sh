#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
# ADR0207: no shared upstream/LFS OAuth identity in Toddy's distributable build.
meson setup /build/compile /src --prefix=/usr --libdir=lib --sysconfdir=/etc --buildtype=release --wrap-mode=nofallback -Ddocumentation=false -Dman=false -Dkerberos=false -Dfedora=false -Dgoabackend=true -Dintrospection=true -Dvapi=true -Dgoogle=false -Dgoogle_client_id= -Dgoogle_client_secret= -Dms_graph=false -Dms_graph_client_id=
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
python3 - <<'PY'
from pathlib import Path
import json
assert json.loads(Path('/build/original-registered-tests.json').read_text())==[], 'Review any original tests before accepting stage'
PY
meson install -C /build/compile --destdir /stage --no-rebuild
LD_LIBRARY_PATH=/stage/usr/lib /stage/usr/libexec/goa-daemon --version > /build/actual-version.log 2>&1
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');version=(w/'actual-version.log').read_text();assert '3.58.1' in version
for relative in ['usr/lib/pkgconfig/goa-1.0.pc','usr/lib/pkgconfig/goa-backend-1.0.pc','usr/lib/girepository-1.0/Goa-1.0.typelib','usr/share/vala/vapi/goa-1.0.vapi']:assert (Path('/stage')/relative).is_file()
config=(w/'compile/config.h').read_text()
for option in ['GOA_GOOGLE_ENABLED','GOA_MS_GRAPH_ENABLED','GOA_KERBEROS_ENABLED','GOA_FEDORA_ENABLED']:assert '#undef '+option in config
for option in ['GOA_GOOGLE_CLIENT_ID','GOA_GOOGLE_CLIENT_SECRET','GOA_MS_GRAPH_CLIENT_ID']:assert '#define '+option+' ""' in config
assert '#define GOA_BACKEND_ENABLED' in config.splitlines()
r={'scope':'Frozen GOA3.58.1 core/backend/GI/Vala SDK and daemon version only; optional Google/Microsoft365 unavailable pending qualified own app identity, no shared OAuth values. Kerberos/Fedora unselected, docs/man omitted. No original tests registered: NOT a test pass. No session-service/account/provider/secret/Settings/GUI acceptance.','compile_exit':0,'stage_exit':0,'original_tests_registered':[],'no_registered_tests_not_a_pass':True,'consumer':{'version':version,'graphical_UI_tested':False},'providers_unavailable':['google','ms_graph','kerberos','fedora'],'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to(w/'stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
PY
