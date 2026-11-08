#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,shlex,subprocess,tempfile
root=Path('/opt/toddy-build');prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
resource_receipt=Path('/var/log/toddy/phase2/desktop-resources-transaction.json')
resources=json.loads(resource_receipt.read_text()) if resource_receipt.exists() else None
integrated=resources is not None and resources['state']=='complete'
version='4.22.4-1+toddy2' if integrated else '4.22.4-1+toddy1'
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gtk'],env=env,text=True)=='install ok installed '+version
assert subprocess.check_output(prefix+['pkg-config','--modversion','gtk4'],env=env,text=True).strip()=='4.22.4'
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
with tempfile.TemporaryDirectory(prefix='toddy-gtk-',dir='/mnt/lfs/tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name;(p/'consumer.c').write_bytes((root/'scripts/build/phase2/gtk-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','gtk4'],env=env,text=True))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    c=subprocess.run(prefix+[native+'/consumer'],env=env,text=True,capture_output=True,check=True)
body='''import gi
gi.require_version('Gtk','4.0');gi.require_version('Gdk','4.0');gi.require_version('Gsk','4.0')
from gi.repository import Gtk,Gdk,Gsk,Gio
assert (Gtk.get_major_version(),Gtk.get_minor_version(),Gtk.get_micro_version())==(4,22,4)
model=Gtk.StringList.new(['Toddy','Português']);assert model.get_n_items()==2 and model.get_string(1)=='Português'
color=Gdk.RGBA();assert color.parse('#002040')
assert Gsk.Transform.__gtype__.name=='GskTransform'
source=Gio.SettingsSchemaSource.get_default();assert source.lookup('org.gtk.gtk4.Settings.FileChooser',False)
print('native-gtk-gdk-gsk-gi-unicode-model-color-owned-schema, no window')
'''
gi=subprocess.run(prefix+['python3','-B','-c',body],env=env,text=True,capture_output=True,check=True)
cache=Path('/mnt/lfs/usr/share/glib-2.0/schemas/gschemas.compiled')
expected=resources['new_schema_cache_sha256'] if integrated else json.loads(Path('/mnt/lfs/sources/phase2/work/gtk-1/test-results.json').read_text())['schema_cache_sha256']
assert hashlib.sha256(cache.read_bytes()).hexdigest()==expected
proof={'scope':'Native installed bootstrap GTK C/GI/model/color/owned schema APIs only; no graphical window/session/media acceptance',
    'native_consumer_exit':0,'stdout':c.stdout,'gi_exit':0,'gi_stdout':gi.stdout,'schema_cache_sha256':expected,
    'pending':'Actual native Wayland/GNOME UI QA, media and integrated icon/MIME/schema registry updates with their package owners'}
Path('/var/log/toddy/phase2/gtk-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
