"""Freeze currently owned GTK3 IM-module inputs for a new private cache job."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2');PKG=Path('/var/log/toddy/packages')
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=Path('/var/log/toddy/build/build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
source=T/'sources/phase2/inputs/gtk3-ibus-cache-1';work=T/'sources/phase2/work/gtk3-ibus-cache-1';receipt=L/'gtk3-ibus-cache-prepared-1.json'
assert not any(p.exists() for p in [source,work,receipt])
assert not list(L.glob('gtk3-ibus-cache-1.*'))
versions=dict(line.split('\t',1) for line in subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Package}\t${Version}\n'],text=True).splitlines())
assert versions['gtk3']=='3.24.52-1+toddy1' and versions['gtk']=='4.22.4-1+toddy6' and versions['ibus']=='1.5.34~rc2-1+toddy1'
records={}
for f in PKG.glob('*.json'):
 r=json.loads(f.read_text())
 if r.get('installed') and versions.get(r['name'])==r['version']:records[r['name']]=r
old=records['gtk3'];cache='/usr/lib/gtk-3.0/3.0.0/immodules.cache';tool='/usr/bin/gtk-query-immodules-3.0'
assert digest(T/cache.lstrip('/'))==old['payload'][cache]['sha256']
assert digest(T/tool.lstrip('/'))==old['payload'][tool]['sha256']
modules={};archives={r['filename'] for r in old['sources']}
for f in (T/'usr/lib/gtk-3.0/3.0.0/immodules').glob('*.so'):
 assert f.is_file() and not f.is_symlink()
 name='/'+str(f.relative_to(T));owners=[r for r in records.values() if name in r['payload']];assert len(owners)==1
 r=owners[0];assert r['name'] in ['gtk3','ibus'] and digest(f)==r['payload'][name]['sha256']
 modules[name]={'owner':r['name'],'version':r['version'],'sha256':digest(f)}
 archives.update(a['filename'] for a in r['sources'])
assert len(modules)==12 and sum(r['owner']=='ibus' for r in modules.values())==1
proof={'modules':modules,'source_archives':sorted(archives),'cache':cache,'tool':tool,'tool_sha256':digest(T/tool.lstrip('/')),'old_cache_sha256':digest(T/cache.lstrip('/')),'old_archive_sha256':old['archive_sha256']}
source.mkdir();shutil.copyfile(T/cache.lstrip('/'),source/'baseline.cache');(source/'toddy-input.json').write_text(json.dumps(proof,indent=2)+'\n')
for p in source.iterdir():p.chmod(0o444)
source.chmod(0o555);work.mkdir();os.chown(work,101,101)
receipt.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'prepared':True,'modules':len(modules),'owners':['gtk3','ibus']}))
