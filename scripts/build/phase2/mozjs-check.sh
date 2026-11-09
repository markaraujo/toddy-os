#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,shlex,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','mozjs'],text=True,env=env)
assert status=='install ok installed 140.17.0-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','mozjs-140'],text=True,env=env).strip()=='140.17.0'
assert subprocess.check_output(prefix+['js140','--version'],text=True,env=env).strip()=='JavaScript-C140.17.0'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-mozjs-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.cpp').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/mozjs-probe.cpp').read_bytes());native='/tmp/'+p.name
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','mozjs-140'],text=True,env=env))
    subprocess.run(prefix+['c++','-std=c++17','-Wall','-Wextra','-Werror',native+'/consumer.cpp',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],env=env,capture_output=True,text=True,check=True)
script="""const date = new Intl.DateTimeFormat('pt-BR',{timeZone:'UTC',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date('2026-11-09T12:00:00Z'));
const parts = new Intl.NumberFormat('en',{style:'unit',unit:'byte'}).formatToParts(1024);
if (date !== '09/11/2026' || !parts.some(p => p.type === 'unit')) throw Error('Desktop Intl consumer');
print('installed PT date/simple unit=42');"""
cli=subprocess.run(prefix+['js140','-e',script],env=env,capture_output=True,text=True,check=True)
assert cli.stdout.strip()=='installed PT date/simple unit=42'
proof={'scope':'Real installed dynamic C++ embedding/GC/typed array/Unicode/Intl/refusal/recovery, shell and desktop PT-date/simple-unit consumer; retained main-suite failures are NOT full Intl qualification','version':'140.17.0','native_consumer_exit':0,'stdout':result.stdout.strip(),'native_cli_exit':0,'cli_stdout':cli.stdout.strip()}
Path('/var/log/toddy/phase2/mozjs-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
