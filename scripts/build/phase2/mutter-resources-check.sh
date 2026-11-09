#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
p=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/tmp','PYTHONDONTWRITEBYTECODE':'1','GI_TYPELIB_PATH':'/usr/lib/mutter-18'}
r=json.loads(Path('/var/log/toddy/phase2/mutter-resources-transaction.json').read_text());assert r['state']=='complete'
for name,version in [('mutter','50.4-1+toddy1'),('gtk','4.22.4-1+toddy4')]:assert subprocess.check_output(p+['dpkg-query','-W','-f=${Status} ${Version}',name],text=True)=='install ok installed '+version
assert not subprocess.check_output(p+['dpkg','--audit'],text=True).strip();subprocess.run(p+['apt-get','check'],check=True)
assert hashlib.sha256(Path('/mnt/lfs/usr/share/glib-2.0/schemas/gschemas.compiled').read_bytes()).hexdigest()==r['new_cache_sha256']
version=subprocess.check_output(p+['mutter','--version'],env=env,text=True);assert version.strip()=='mutter 50.4'
code="""import gi,json
for name in ['Mtk','Cogl','Clutter','Meta']:gi.require_version(name,'18')
from gi.repository import Mtk,Cogl,Clutter,Meta,Gio
source=Gio.SettingsSchemaSource.get_default();fixed,rel=source.list_schemas(False)
assert len(fixed)==61 and len(rel)==6
for name in ['org.gnome.mutter','org.gnome.mutter.keybindings','org.gnome.mutter.wayland','org.gnome.mutter.wayland.keybindings','org.freedesktop.ColorHelper']:assert source.lookup(name,False) is not None
print(json.dumps({'native_gi_exit':0,'native_schema_exit':0,'fixed_schemas':len(fixed),'relocatable_schemas':len(rel)}))
"""
proof=json.loads(subprocess.check_output(p+['python3','-c',code],env=env,text=True));proof.update(scope='Native installed Mutter Wayland bootstrap CLI/GI/shared schema ownership only; actual compositor/window/session still pending',version=version.strip(),old_gtk_nonlegal_regular_files_unchanged=r['old_gtk_nonlegal_regular_files_unchanged'])
Path('/var/log/toddy/phase2/mutter-resources-installed-consumer.json').write_text(json.dumps(proof,indent=2)+'\n')
PY
