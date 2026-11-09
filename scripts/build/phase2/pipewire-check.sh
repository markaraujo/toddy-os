#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
unshare --mount --propagation private bash -c '
mount -t proc -o nosuid,nodev,noexec proc /mnt/lfs/proc
mount -t tmpfs -o nosuid,nodev,mode=1777,size=32m tmpfs /mnt/lfs/dev/shm
exec python3 -
' <<'PY'
from pathlib import Path
import json,os,shlex,subprocess,tempfile,time,stat
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','pipewire'],env=env,text=True)=='install ok installed 1.6.8-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','libpipewire-0.3'],env=env,text=True).strip()=='1.6.8'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
logs=Path('/var/log/toddy/phase2')
with tempfile.TemporaryDirectory(prefix='toddy-pipewire-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);p.chmod(0o755);native='/tmp/'+p.name
    (p/'consumer.c').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/pipewire-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','libpipewire-0.3'],env=env,text=True))
    subprocess.run(prefix+['cc','-std=c11','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    runtime=p/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,101,101)
    env['XDG_RUNTIME_DIR']=native+'/runtime'
    user=['/usr/bin/setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101','/mnt/lfs']
    with (logs/'pipewire-installed-daemon-v3.log').open('xb') as log:
        daemon=subprocess.Popen(user+['pipewire'],env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                assert daemon.poll() is None,'Installed private daemon exited before socket'
                if (runtime/'pipewire-0').exists():break
                time.sleep(.05)
            assert stat.S_ISSOCK((runtime/'pipewire-0').stat().st_mode)
            status=dict(line.split(':',1) for line in Path('/proc',str(daemon.pid),'status').read_text().splitlines() if ':' in line)
            assert set(status['Uid'].split())=={'101'} and int(status['CapEff'],16)==0 and status['NoNewPrivs'].strip()=='1'
            consumer=subprocess.run(user+[native+'/consumer'],env=env,capture_output=True,text=True,timeout=15,check=True)
            dump=subprocess.check_output(user+['pw-dump'],env=env,timeout=15,text=True)
            assert any(r['type']=='PipeWire:Interface:Core' for r in json.loads(dump))
        finally:
            daemon.terminate()
            try:daemon_exit=daemon.wait(timeout=10)
            except subprocess.TimeoutExpired:daemon.kill();daemon.wait();raise
    (logs/'pipewire-installed-core-dump.json').write_text(dump)
    (logs/'pipewire-installed-consumer.json').write_text(json.dumps({
        'scope':'Actual installed private UID101/NNP daemon/client core synchronization only; no audible sound, session routing or desktop acceptance',
        'native_consumer_exit':0,'stdout':consumer.stdout,'daemon_stopped':True,'daemon_exit':daemon_exit,
        'runtime_uid':101,'runtime_nnp':True},indent=2)+'\n')
PY
