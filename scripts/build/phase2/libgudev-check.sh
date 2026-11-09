#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,shlex,subprocess,tempfile
name='libgudev';version='238';pc='gudev-1.0'
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True,env=env)
assert status=='install ok installed '+version+'-1+toddy1',status
assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True,env=env).strip()==version
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-'+name+'-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_bytes((root/'scripts/build/phase2'/(name+'-probe.c')).read_bytes());native='/tmp/'+p.name
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs',pc],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],env=env,check=True,capture_output=True,text=True)
gi_script="import gi;gi.require_version('GUdev','1.0');from gi.repository import GUdev;c=GUdev.Client.new(None);assert c is not None;assert c.query_by_sysfs_path('/sys/devices/toddy-nonexistent') is None"
subprocess.run(prefix+['python3','-c',gi_script],env=env,check=True)
proof={'scope':'Native installed GUdev client/enumerator/filter lifecycle/negative queries and GI; no real device/event/GNOME acceptance','name':name,'version':version,'native_consumer_exit':0,'stdout':result.stdout.strip()}
Path('/var/log/toddy/phase2',name+'-installed-consumer.json').write_text(json.dumps(proof,indent=2)+chr(10))
CHECK
