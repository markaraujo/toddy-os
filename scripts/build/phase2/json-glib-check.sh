#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,shlex,subprocess,tempfile
name='json-glib';version='1.10.8';pc='json-glib-1.0'
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True,env=env)
assert status=='install ok installed '+version+'-1+toddy1',status
assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True,env=env).strip()==version
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-'+name+'-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_bytes((root/'scripts/build/phase2'/(name+'-probe.c')).read_bytes());native='/tmp/'+p.name
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs',pc,'gio-2.0'],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],env=env,check=True,capture_output=True,text=True)
gi_script="import gi;gi.require_version('Json','1.0');from gi.repository import Json;p=Json.Parser.new();assert p.load_from_data('{\"state\":\"offline\"}',-1);assert p.get_root().get_object().get_string_member('state')=='offline'"
subprocess.run(prefix+['python3','-c',gi_script],env=env,check=True)
proof={'scope':'Native installed JSON-GLib Unicode/typed object/parser refusal and GIR API; no desktop/network/service acceptance','name':name,'version':version,'native_consumer_exit':0,'stdout':result.stdout.strip()}
Path('/var/log/toddy/phase2',name+'-installed-consumer.json').write_text(json.dumps(proof,indent=2)+chr(10))
CHECK
