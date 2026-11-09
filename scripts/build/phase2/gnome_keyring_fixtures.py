"""Run five upstream fixture-only programs in a private test-hook-enabled build."""
from pathlib import Path
import hashlib,json,re,subprocess
p=Path('/build');assert not (p/'fixture-debug').exists() and not (p/'fixture-results-2.json').exists()
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def production_artifacts():return {str(f.relative_to(p/'compile')):digest(f) for f in (p/'compile').rglob('*') if f.is_file() and not f.is_symlink() and f.open('rb').read(4)==b'\x7fELF'}
before=production_artifacts();assert before
rows=[json.loads(s) for s in (p/'compile/meson-logs/testlog.json').read_text().splitlines() if s.strip()]
names=['dbus-search','dbus-items','dbus-signals','dbus-lock','dbus-portal']
passed=[r for r in rows if r['result']=='OK' and r['returncode']==0];assert len(passed)==57
if len(rows)==62:
 failed=[r for r in rows if r['result']!='OK'];assert len(failed)==5 and {r['name'].rsplit(':',1)[-1] for r in failed}==set(names) and all(r['result']=='TIMEOUT' for r in failed)
else:assert len(rows)==57 and not any(r['name'].rsplit(':',1)[-1] in names for r in rows)
(p/'production-testlog-before-fixtures-2.json').write_bytes((p/'compile/meson-logs/testlog.json').read_bytes())
(p/'production-elfs-before-fixtures-2.json').write_text(json.dumps(before,indent=2)+'\n')
production_options={r['name']:r['value'] for r in json.loads((p/'compile/meson-info/intro-buildoptions.json').read_text())};assert production_options['debug-mode'] is False
command=['meson','setup','/build/fixture-debug','/src','--prefix=/usr','--libdir=lib','--libexecdir=libexec','--sysconfdir=/etc','--localstatedir=/var','--buildtype=release','--wrap-mode=nodownload','-Dlibcap-ng=disabled','-Dselinux=disabled','-Dssh-agent=false','-Dsystemd=enabled','-Dpam=true','-Ddebug-mode=true','-Dmanpage=false']
subprocess.run(command,check=True)
fixture_options={r['name']:r['value'] for r in json.loads((p/'fixture-debug/meson-info/intro-buildoptions.json').read_text())}
for name in ['libcap-ng','selinux','ssh-agent','systemd','pam','manpage','buildtype','prefix','libdir','libexecdir','sysconfdir','localstatedir']:assert production_options[name]==fixture_options[name]
assert fixture_options['debug-mode'] is True
registered=json.loads((p/'compile/meson-info/intro-tests.json').read_text());targets=[str(Path(t['cmd'][0]).relative_to('/build/compile')) for t in registered if t['name'] in names];assert len(targets)==5
subprocess.run(['ninja','-C','/build/fixture-debug','-j4','daemon/gnome-keyring-daemon','schema/gschemas.compiled',*targets],check=True)
runs=[]
for name in names:
 with (p/('fixture-2-'+name+'.log')).open('x') as log:r=subprocess.run(['dbus-run-session','--','meson','test','-C','/build/fixture-debug','--no-rebuild','--print-errorlogs','-j1',name],stdout=log,stderr=subprocess.STDOUT)
 records=[json.loads(s) for s in (p/'fixture-debug/meson-logs/testlog.json').read_text().splitlines() if s.strip()];assert len(records)==1
 (p/('fixture-2-'+name+'.json')).write_text(json.dumps(records[0],indent=2)+'\n')
 runs.append({'name':name,'exit':r.returncode,'result':records[0]['result'],'returncode':records[0]['returncode'],'log_sha256':digest(p/('fixture-2-'+name+'.log')),'record_sha256':digest(p/('fixture-2-'+name+'.json'))})
assert production_artifacts()==before
result={'scope':'Five original fixture-only tests against PRIVATE WITH_DEBUG daemon, never staged.57production original programs reused and all production ELF bytes unchanged; production service/PAM/GUI acceptance separate','production_original_programs':57,'fixture_programs':runs,'production_elfs_unchanged':before,'fixture_daemon_sha256':digest(p/'fixture-debug/daemon/gnome-keyring-daemon'),'fixture_debug_mode':True,'production_debug_mode':False,'fixture_never_staged':True}
(p/'fixture-results-2.json').write_text(json.dumps(result,indent=2)+'\n');assert all(r['exit']==0 and r['result']=='OK' and r['returncode']==0 for r in runs),'Original fixture failures retained, never accepted by timeout'
