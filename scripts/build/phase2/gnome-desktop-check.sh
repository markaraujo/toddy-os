#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'CHECK'
from pathlib import Path
import json,shlex,subprocess,tempfile
name='gnome-desktop';version='44.5';pc='gnome-desktop-4'
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
status=subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True,env=env)
assert status=='install ok installed '+version+'-1+toddy1',status
assert subprocess.check_output(prefix+['pkg-config','--modversion',pc],text=True,env=env).strip()==version
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-'+name+'-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_text((root/'scripts/build/phase2'/(name+'-probe.c')).read_text().replace('\"pt_BR.UTF-8\",\"C\"','\"pt_BR.UTF-8\",\"C.UTF-8\"').replace('strcmp(language,\"Portuguese\")==0','(strcmp(language,\"Portuguese\")==0 || strcmp(language,\"Portuguese (Brazil)\")==0)').replace('strcmp(country,\"Brazil\")==0','(strcmp(country,\"Brazil\")==0 || strcmp(country,\"Brazil (Portuguese)\")==0)'));native='/tmp/'+p.name
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs',pc,'gio-2.0'],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],env=env,check=True,capture_output=True,text=True)
gi_script="import gi;gi.require_version('GnomeDesktop','4.0');gi.require_version('GnomeBG','4.0');gi.require_version('GnomeRR','4.0');from gi.repository import GnomeDesktop,GnomeBG,GnomeRR;assert GnomeDesktop.XkbInfo is not None"
subprocess.run(prefix+['python3','-c',gi_script],env=env,check=True)
proof={'scope':'Native installed GNOME Desktop ISO/keyboard/common APIs/GIR import; no actual session, keyboard events, thumbnail sandbox or async background GI acceptance','name':name,'version':version,'native_consumer_exit':0,'stdout':result.stdout.strip()}
Path('/var/log/toddy/phase2',name+'-installed-consumer.json').write_text(json.dumps(proof,indent=2)+chr(10))
CHECK
