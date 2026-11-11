"""Prepare immutable public schema inputs for a same-version GTK cache update."""
from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess
TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=Path('/var/log/toddy/build/build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
source=TARGET/'sources/phase2/inputs/settings-schema-union-1';work=TARGET/'sources/phase2/work/settings-schema-union-1';receipt=LOG/'settings-schema-union-prepared-1.json'
assert not any(p.exists() for p in [source,work,receipt])
assert not list(LOG.glob('settings-schema-union-1.*'))
native=json.loads(Path('/var/log/toddy/build/b02-gnome-control-center-install.success.json').read_text())
assert native['recipe_exit']==native['postcheck_exit']==0
old=json.loads(Path('/var/log/toddy/packages/gtk_4.22.4-1+toddy9_amd64.json').read_text());assert old['installed']
assert subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Version}','gtk'],text=True)=='4.22.4-1+toddy9'
directory=TARGET/'usr/share/glib-2.0/schemas';cache=directory/'gschemas.compiled'
assert not cache.is_symlink() and digest(cache)==old['payload']['/usr/share/glib-2.0/schemas/gschemas.compiled']['sha256']
versions=dict(line.split('\t',1) for line in subprocess.check_output(['chroot',str(TARGET),'dpkg-query','-W','-f=${Package}\t${Version}\n'],text=True).splitlines())
records={}
for f in Path('/var/log/toddy/packages').glob('*.json'):
    r=json.loads(f.read_text())
    if not r.get('installed'):continue
    # Only the actual current version, never an older retained archive record.
    if versions.get(r['name'])==r['version']:records[r['name']]=r
inputs={};owners={};archives={r['filename'] for r in old['sources']}
for f in directory.iterdir():
    if f.name=='gschemas.compiled':continue
    assert f.is_file() and not f.is_symlink()
    assert f.name=='gschema.dtd' or f.name.endswith(('.gschema.xml','.enums.xml','.gschema.override')),f.name
    name='/'+str(f.relative_to(TARGET));candidates=[r for r in records.values() if name in r['payload']]
    assert len(candidates)==1,(name,[r['name'] for r in candidates])
    owner=candidates[0];assert digest(f)==owner['payload'][name]['sha256']
    inputs[f.name]=digest(f);owners[f.name]={'name':owner['name'],'version':owner['version']}
    archives.update(r['filename'] for r in owner['sources'])
proof={'scope':'Read-only public stock schema inputs; no user settings or installed mutation', 'inputs':inputs,'owners':owners,'source_archives':sorted(archives),'old_cache_sha256':digest(cache),'old_gtk_archive_sha256':old['archive_sha256']}
source.mkdir();(source/'schemas').mkdir()
for name in inputs:shutil.copyfile(directory/name,source/'schemas'/name)
shutil.copyfile(cache,source/'baseline-gschemas.compiled')
(source/'toddy-schema-union.json').write_text(json.dumps(proof,indent=2)+'\n')
for f in source.rglob('*'):f.chmod(0o555 if f.is_dir() else 0o444)
source.chmod(0o555);work.mkdir();os.chown(work,101,101)
receipt.write_text(json.dumps({'source':str(source),'work':str(work),**proof},indent=2)+'\n')
print(json.dumps({'prepared':True,'inputs':len(inputs),'source_owners':len({o['name'] for o in owners.values()})}))
