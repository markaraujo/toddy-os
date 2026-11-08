#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,hashlib,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
for name,version in [('librsvg','2.62.3-1+toddy1'),('gdk-pixbuf','2.44.7-1+toddy2')]:
    assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',name],env=env,text=True)=='install ok installed '+version
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-svg-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/librsvg-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','librsvg-2.0','gdk-pixbuf-2.0'],env=env,text=True))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    c=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
body='''import gi
gi.require_version('Rsvg','2.0');gi.require_version('GdkPixbuf','2.0')
from gi.repository import Rsvg,GdkPixbuf
data=b"<svg xmlns='http://www.w3.org/2000/svg' width='8' height='8'><rect width='8' height='8' fill='#002040'/></svg>"
h=Rsvg.Handle.new_from_data(data);assert h
loader=GdkPixbuf.PixbufLoader.new_with_type('svg');assert loader.write(data) and loader.close()
p=loader.get_pixbuf();assert p.get_width()==p.get_height()==8 and bytes(p.get_pixels())[:3]==bytes([0,32,64])
ok,png=p.save_to_bufferv('png',[],[]);assert ok
loader=GdkPixbuf.PixbufLoader.new_with_type('png');assert loader.write(png) and loader.close()
assert bytes(loader.get_pixbuf().get_pixels())[:3]==bytes([0,32,64])
print('native-rsvg-gi-svg-pixels-and-png-roundtrip')
'''
gi=subprocess.run(prefix+['python3','-B','-c',body],env=env,text=True,capture_output=True,check=True)
receipt=json.loads(Path('/var/log/toddy/phase2/librsvg-gdk-cache-transaction.json').read_text());assert receipt['complete']
cache=Path('/mnt/lfs/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache')
assert hashlib.sha256(cache.read_bytes()).hexdigest()==receipt['new_cache_sha256']
proof={'scope':'Actual installed native SVG/Cairo/Gdk loader/generated owned cache and GI SVG+PNG pixel roundtrip; no graphical window/session acceptance',
       'native_consumer_exit':0,'stdout':c.stdout,'gi_exit':0,'gi_stdout':gi.stdout,'cache_transaction':receipt}
Path('/var/log/toddy/phase2/librsvg-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
