#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release --wrap-mode=nofallback -Dexamples=false -Dgtk_doc=false -Dvapi=true -Dsoup2=false
ninja -C /build/compile -j4 > /build/original-build.log 2>&1
meson introspect /build/compile --tests > /build/original-registered-tests.json
meson test -C /build/compile --no-rebuild --print-errorlogs --timeout-multiplier=1 --suite rest > /build/original-local-tests.log 2>&1
# Flickr's URL construction case is local; its other case and LastFM contact external services.
/build/compile/tests/flickr -p /flickr/test_build_login_url > /build/original-flickr-local.log 2>&1
meson install -C /build/compile --destdir /stage --no-rebuild
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
w=Path('/build');tests=[json.loads(x) for x in (w/'compile/meson-logs/testlog.json').read_text().splitlines() if x.strip()]
assert len(tests)==7 and all(x['result']=='OK' and x['returncode']==0 for x in tests)
assert 'ok 1 /flickr/test_build_login_url' in (w/'original-flickr-local.log').read_text()
assert Path('/stage/usr/lib/pkgconfig/rest-1.0.pc').is_file() and Path('/stage/usr/share/vala/vapi/rest-1.0.vapi').is_file()
r={'scope':'Frozen BLFS13.1 librest0.10.2/Soup3 shared/GI/Vala SDK; seven original local programs plus one original Flickr URL case. External-service Flickr/LastFM cases deliberately unexecuted, no credentials/network/provider/account/GUI acceptance.','compile_exit':0,'stage_exit':0,'tests':tests,'flickr_local_case':True,'unexecuted_external_cases':['/flickr/flickr','/lastm/lastfm'],'artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to(w/'stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n')
s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=16*1024**3
PY
