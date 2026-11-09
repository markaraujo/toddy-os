#!/bin/bash
set -euo pipefail
[[ $(id -u) == 101 && ! -e /build/compile ]]
meson setup /build/compile /src --prefix=/usr --libdir=lib --buildtype=release \
    --wrap-mode=nofallback -Dauto_features=disabled -Dtests=enabled -Dexamples=disabled \
    -Dsession-managers=[] -Dlibsystemd=enabled -Dlogind=enabled -Ddbus=enabled \
    -Dudev=enabled -Dalsa=enabled -Dpipewire-alsa=enabled -Dflatpak=enabled \
    -Dsystemd-user-service=enabled -Dsystemd-system-service=disabled \
    -Dpipewire-jack=disabled -Dpipewire-v4l2=disabled -Drlimits-install=false \
    -Dpam-defaults-install=false -Dlegacy-rtkit=false \
    > /build/configure.log 2>&1
ninja -C /build/compile -j4 > /build/compile.log 2>&1
meson test -C /build/compile --no-rebuild --print-errorlogs > /build/upstream-tests.log 2>&1
DESTDIR=/stage meson install -C /build/compile --no-rebuild > /build/stage.log 2>&1
cc -std=c11 -Wall -Wextra -Werror /src/toddy-probe.c \
    -I/stage/usr/include/pipewire-0.3 -I/stage/usr/include/spa-0.2 \
    -L/stage/usr/lib -Wl,-rpath,/stage/usr/lib -lpipewire-0.3 -o /build/consumer
python3 - <<'PY'
from pathlib import Path
import json,os,stat,subprocess,time
work=Path('/build');runtime=work/'runtime';runtime.mkdir(mode=0o700)
env=dict(os.environ,XDG_RUNTIME_DIR=str(runtime),PIPEWIRE_MODULE_DIR='/stage/usr/lib/pipewire-0.3',
         SPA_PLUGIN_DIR='/stage/usr/lib/spa-0.2',PIPEWIRE_CONFIG_DIR='/stage/usr/share/pipewire',LD_LIBRARY_PATH='/stage/usr/lib')
with (work/'daemon.log').open('xb') as log:
    daemon=subprocess.Popen(['/stage/usr/bin/pipewire'],env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            assert daemon.poll() is None,'Private daemon exited before socket'
            if (runtime/'pipewire-0').exists():break
            time.sleep(.05)
        assert stat.S_ISSOCK((runtime/'pipewire-0').stat().st_mode)
        with (work/'consumer.log').open('xb') as output:
            subprocess.run(['/build/consumer'],env=env,stdout=output,stderr=subprocess.STDOUT,timeout=15,check=True)
        dump=subprocess.check_output(['/stage/usr/bin/pw-dump'],env=env,timeout=15,text=True)
        rows=json.loads(dump);assert any(r['type']=='PipeWire:Interface:Core' for r in rows)
        (work/'core-dump.json').write_text(dump)
    finally:
        daemon.terminate()
        try:code=daemon.wait(timeout=10)
        except subprocess.TimeoutExpired:daemon.kill();daemon.wait();raise
        (work/'daemon.exit').write_text(str(code)+'\n')
rows=[json.loads(s) for s in (work/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
assert rows and all((r['result']=='OK' and r['returncode']==0) or (r['result']=='SKIP' and r['returncode']==77) for r in rows)
(work/'test-results.json').write_text(json.dumps({'scope':'Native Pipewire private daemon/client core and original tests; no audible, physical, routing/session-manager or GNOME acceptance',
    'upstream_drivers':[{'name':r['name'],'result':r['result'],'exit':r['returncode']} for r in rows],
    'staged_daemon_client_exit':0,'private_runtime':True,'daemon_stopped':True,
    'profile':'ALSA/udev/systemd/logind/DBus/Flatpak integration; no bundled Wireplumber, JACK/V4L2 compatibility or PAM limit modifications'},indent=2)+'\n')
PY
