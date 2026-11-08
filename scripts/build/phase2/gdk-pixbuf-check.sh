#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs']
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gdk-pixbuf'],text=True,env=env)=='install ok installed 2.44.7-1+toddy1'
assert subprocess.check_output(prefix+['pkg-config','--modversion','gdk-pixbuf-2.0'],text=True,env=env).strip()=='2.44.7'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-pixbuf-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);(p/'consumer.c').write_bytes((root/'scripts/build/phase2/gdk-pixbuf-probe.c').read_bytes());native='/tmp/'+p.name
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','gdk-pixbuf-2.0','gio-2.0'],text=True,env=env))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    result=subprocess.run(prefix+[native+'/consumer'],text=True,capture_output=True,env=env,check=True)
body='''import gi
gi.require_version('GdkPixbuf','2.0')
from gi.repository import GdkPixbuf
p=GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB,True,8,2,2);p.fill(0x001020ff)
ok,data=p.save_to_bufferv('png',[],[]);assert ok and data
loader=GdkPixbuf.PixbufLoader.new_with_type('png');assert loader.write(data) and loader.close()
decoded=loader.get_pixbuf();assert decoded.get_width()==decoded.get_height()==2
assert bytes(decoded.get_pixels())[:4]==bytes([0,16,32,255])
print('native-pixbuf-gi-png-pixels')
'''
gi=subprocess.run(prefix+['python3','-B','-c',body],text=True,capture_output=True,env=env,check=True)
cache=Path('/mnt/lfs/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache')
assert cache.is_file() and all(not l.strip() or l.startswith('#') for l in cache.read_text().splitlines())
proof={'scope':'Native installed image APIs, generated cache and actual GI PNG pixel roundtrip; no graphical window acceptance',
    'version':'2.44.7','native_consumer_exit':0,'stdout':result.stdout,'gi_exit':0,'gi_stdout':gi.stdout,
    'cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'builtin_loaders':['png','jpeg','gif'],'external_loaders':0}
Path('/var/log/toddy/phase2/gdk-pixbuf-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
