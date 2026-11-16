#!/bin/bash
# Qualified private compiler only; no daemon, model, provider or installed write.
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile && -r /src/meson.build ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dauto_features=disabled -Dtests=disabled -Dexamples=disabled \
    -Dsession-managers=[] -Dpw-cat=enabled -Dsndfile=enabled -Dpw-cat-ffmpeg=disabled \
    > /build/configure.log 2>&1
# Build this one upstream target and its private internal link prerequisites.
ninja -C /build/compile -j4 src/tools/pw-cat > /build/compile.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild --tags toddy-pw-cat \
    > /build/stage.log 2>&1
# Only the upstream binary is tagged; full libraries/configs are never staged.
[[ -x /stage/usr/bin/pw-cat ]]
/stage/usr/bin/pw-cat --help > /build/pw-cat-help.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json,os,subprocess
stage=Path('/stage');leaves=[p for p in stage.rglob('*') if not p.is_dir()]
assert leaves==[stage/'usr/bin/pw-cat'] and not leaves[0].is_symlink()
help=Path('/build/pw-cat-help.log').read_text();assert help.strip()
version=subprocess.check_output(['/stage/usr/bin/pw-cat','--version'],text=True,timeout=15)
assert 'Compiled with libpipewire 1.6.8' in version and 'Linked with libpipewire 1.6.8' in version
Path('/build/pw-cat-version.log').write_text(version)
for alias in ['pw-play','pw-record','pw-midiplay','pw-midirecord','pw-midi2play','pw-midi2record','pw-dsdplay','pw-encplay','pw-sysex']:
 os.symlink('pw-cat',stage/'usr/bin'/alias)
 result=subprocess.run([str(stage/'usr/bin'/alias),'--help'],capture_output=True,text=True,timeout=15)
 assert result.returncode==0 and (result.stdout+result.stderr).strip()
 Path('/build/'+alias+'-help.log').write_text(result.stdout+result.stderr)
Path('/build/tool-qualified.json').write_text(json.dumps({'upstream':'1.6.8','target':'src/tools/pw-cat','install_tag':'toddy-pw-cat',
 'options':{'pw-cat':'enabled','sndfile':'enabled','pw-cat-ffmpeg':'disabled'},'help_exit':0,
 'aliases':['pw-play','pw-record','pw-midiplay','pw-midirecord','pw-midi2play','pw-midi2record','pw-dsdplay','pw-encplay','pw-sysex'],
 'scope':'Actual native help consumers only; capture/playback and routing remain pending'},sort_keys=True)+'\n')
PY
