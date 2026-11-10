#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
[[ $(stat -c %d /build) != $(stat -c %d /usr) ]]
export PYTHONDONTWRITEBYTECODE=1
ulimit -c 0
mkdir /build/compile
cd /build/compile
/src/configure --prefix=/usr --libdir=/usr/lib --disable-static --enable-introspection=yes > /build/configure.log 2>&1
make -j4 > /build/original-build.log 2>&1
# Frozen book: no original test suite; an empty make check is not evidence.
# Keep the upstream chown/chmod hook grouped: shell && would otherwise run
# chmod4755 even after a successful nonempty DESTDIR test skips chown.
python3 - <<'PY'
from pathlib import Path
p=Path('/build/compile/src/daemon/Makefile');s=p.read_text()
lines=[line for line in s.splitlines() if line.startswith('\t-test -n "$(DESTDIR)" || ')]
assert len(lines)==1 and 'chown root' in lines[0] and 'chmod 4755' in lines[0]
prefix,body=lines[0].split(' || ',1)
p.write_text(s.replace(lines[0],prefix+' || { '+body+'; }'))
PY
make DESTDIR=/stage install > /build/original-stage.log 2>&1
cc /src/toddy-probe.c -I/stage/usr/include/libgtop-2.0 -L/stage/usr/lib \
   $(PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --cflags --libs libgtop-2.0) -o /build/local-probe
LD_LIBRARY_PATH=/stage/usr/lib /build/local-probe > /build/local-probe.log
PKG_CONFIG_PATH=/stage/usr/lib/pkgconfig pkg-config --modversion libgtop-2.0 > /build/actual-version.log
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,stat
w=Path('/build');assert (w/'actual-version.log').read_text().strip()=='2.41.3'
consumer=(w/'local-probe.log').read_text();assert consumer=='Libgtop direct local memory/uptime/own-process/missing-PID refusal/two recoveries; no server or elevated identity\n'
assert Path('/stage/usr/share/gir-1.0/GTop-2.0.gir').is_file()
# Upstream deliberately skips its chown/chmod4755 hook for DESTDIR installs.
for p in Path('/stage').rglob('*'):
 assert not p.lstat().st_mode & (stat.S_ISUID|stat.S_ISGID)
assert Path('/stage/usr/libexec/libgtop_server2').stat().st_mode&0o7777==0o755
r={'scope':'Frozen libgtop2.41.3 shared library/GI/helper payload compiled; upstream has no test suite, not an upstream suite pass. Actual direct local memory/uptime/own-process API with absent-PID refusal/two recoveries under UID101. DESTDIR leaves helpers0755, no setuid/server activation. No remote/helper protocol/privileged process/Settings GUI/desktop-resource/physical acceptance.','compile_exit':0,'stage_exit':0,'original_test_suite_available':False,'consumer':consumer,'version':'2.41.3','artifacts':{str(p.relative_to(w/'compile')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'compile').rglob('*') if p.is_file() and not p.is_symlink() and p.open('rb').read(4)==b'\x7fELF'},'stage_sha256':{str(p.relative_to('/stage')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/stage').rglob('*') if p.is_file() and not p.is_symlink()}}
(w/'stage-results.json').write_text(json.dumps(r,indent=2)+'\n');s=os.statvfs('/build');assert s.f_bavail*s.f_frsize>=512*1024**2
PY
