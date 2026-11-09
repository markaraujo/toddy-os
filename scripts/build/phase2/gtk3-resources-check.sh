#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shlex,subprocess,tempfile
target=Path('/mnt/lfs');logs=Path('/var/log/toddy/phase2')
prefix=['chroot',str(target)]
env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root','PYTHONDONTWRITEBYTECODE':'1'}
receipt=json.loads((logs/'gtk3-resources-transaction.json').read_text())
assert receipt['state']=='complete'
for package,version in [('gtk3','3.24.52-1+toddy1'),('gtk','4.22.4-1+toddy3')]:
    assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}',package],env=env,text=True)=='install ok installed '+version
assert not subprocess.check_output(prefix+['dpkg','--audit'],env=env,text=True).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
cache='usr/share/glib-2.0/schemas/gschemas.compiled'
imcache='usr/lib/gtk-3.0/3.0.0/immodules.cache'
assert sha(target/cache)==receipt['new_cache_sha256']
assert sha(target/imcache)==receipt['immodules_cache_sha256']
inputs={p.name:sha(p) for p in (target/Path(cache).parent).iterdir() if p.is_file() and p.name!='gschemas.compiled'}
assert inputs==receipt['schema_inputs']
old=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy2_amd64.json').read_text())
verified=0
for name,row in old['payload'].items():
    if name=='/'+cache or name=='/usr/share/doc/gtk' or name.startswith('/usr/share/doc/gtk/'):continue
    path=target/name.lstrip('/');st=path.lstat()
    assert st.st_mode==row['mode'] and st.st_uid==row['uid'] and st.st_gid==row['gid']
    if 'sha256' in row:assert path.is_file() and not path.is_symlink() and sha(path)==row['sha256'];verified+=1
    elif 'symlink' in row:assert path.is_symlink() and os.readlink(path)==row['symlink']
    else:assert row['directory'] and path.is_dir()
with tempfile.TemporaryDirectory(prefix='toddy-gtk3-',dir=target/'tmp') as directory:
    p=Path(directory);native='/tmp/'+p.name
    (p/'consumer.c').write_bytes(Path('/opt/toddy-build/scripts/build/phase2/gtk3-probe.c').read_bytes())
    flags=shlex.split(subprocess.check_output(prefix+['pkg-config','--cflags','--libs','gtk+-3.0'],env=env,text=True))
    subprocess.run(prefix+['cc','-Wall','-Wextra','-Werror',native+'/consumer.c',*flags,'-o',native+'/consumer'],env=env,check=True)
    consumer=subprocess.run(prefix+[native+'/consumer'],env=env,capture_output=True,text=True,check=True)
gi_script="""import gi,json
gi.require_version('Gtk','3.0');gi.require_version('Gdk','3.0')
from gi.repository import Gtk,Gdk,Gio
assert (Gtk.get_major_version(),Gtk.get_minor_version(),Gtk.get_micro_version())==(3,24,52)
a=Gtk.Adjustment.new(42,0,100,1,10,0);assert a.get_value()==42
c=Gdk.RGBA();assert c.parse('#002040')
s=Gio.SettingsSchemaSource.get_default();fixed,relocatable=s.list_schemas(True)
assert len(fixed)==56 and len(relocatable)==6
for name in ['org.gtk.Settings.FileChooser','org.gtk.gtk4.Settings.FileChooser','org.gnome.desktop.interface']:
 assert s.lookup(name,True) is not None
print(json.dumps({'fixed':len(fixed),'relocatable':len(relocatable)}))
"""
gi_result=json.loads(subprocess.check_output(prefix+['python3','-c',gi_script],env=env,text=True))
work=target/'sources/phase2/work/gtk3-resources-1'
resources=json.loads((work/'test-results.json').read_text())
modules=sorted('/'+p for p in resources['immodules'])
for p,h in resources['immodules'].items():assert sha(target/p)==h
query=subprocess.run(prefix+['/usr/bin/gtk-query-immodules-3.0',*modules],env=env,text=True,capture_output=True,check=True)
assert not query.stderr.strip()
def data(text):return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
assert data(query.stdout)==data((target/imcache).read_text())
result={'scope':'Native installed GTK3/GDK/GI/non-widget APIs, shared schemas and IM metadata; no actual window/display/IME input/GDM/GNOME acceptance',
        'installed_c_exit':0,'installed_gi_exit':0,'native_schema_counts':gi_result,
        'immodules_query_exit':0,'immodules':len(modules),
        'gtk4_nonlegal_regular_files_unchanged':verified,'gtk4_library_rebuild':False,
        'stdout':consumer.stdout.strip()}
(logs/'gtk3-installed-consumer.json').write_text(json.dumps(result,indent=2)+'\n')
PY
