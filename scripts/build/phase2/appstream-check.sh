#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','appstream'],env=env,text=True)=='install ok installed 1.1.6-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','appstream'],env=env,text=True).strip()=='1.1.6'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-appstream-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/appstream-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','appstream'],env=env,text=True))
    subprocess.run(prefix+['cc','-std=c11','-D_GNU_SOURCE','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    r=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
subprocess.run(prefix+['python3','-B','-c',"import gi;gi.require_version('AppStream','1.0');from gi.repository import AppStream;c=AppStream.Component.new();c.set_id('org.toddy.NativeProbe');assert c.get_id()=='org.toddy.NativeProbe'"],env=env,check=True)
Path('/var/log/toddy/phase2/appstream-installed-consumer.json').write_text(json.dumps({'scope':'Native installed AppStream UTF8 metadata/refusal/GI bootstrap, not graphical/catalog acceptance',
    'native_consumer_exit':0,'stdout':r.stdout,'stderr':r.stderr,'gi_exit':0,'unicode_metadata':True,'malformed_xml_refusal':True},indent=2)+'\n')
PY
