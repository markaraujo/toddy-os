#!/usr/bin/env python3
"""Add the already upstream-pinned GVDB source to a new immutable DConf input."""
import hashlib,json,shlex,subprocess,sys
from pathlib import Path
import phase2_vm

def main():
    root=phase2_vm.ROOT
    rows=json.loads((root/'config/phase2/sources.lock.json').read_text())['components']
    extra=next(r for r in rows if r['name']=='dconf-gvdb')
    archive=(root/'.local/sources'/extra['filename']).read_bytes();assert hashlib.sha256(archive).hexdigest()==extra['sha256']
    recipe=(root/'scripts/build/phase2/dconf-build.sh').read_text()
    finish=sys.argv[1:]==['--finish-existing'];assert not sys.argv[1:] or finish
    code='''from pathlib import Path
import fcntl,hashlib,json,os,shutil,subprocess,sys,time,tarfile
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'extra={extra!r}\nrecipe={recipe!r}\nfinish={finish!r}\n'+'''
base=Path('/mnt/lfs/sources');log=Path('/var/log/toddy/phase2')
assert (log/'dconf-1.exit').read_text().strip()=='1'
assert "Dependency 'gvdb' is required but not found" in (log/'dconf-1.log').read_text()
original=base/'phase2/inputs/dconf-0.49.0';source=base/'phase2/inputs/dconf-0.49.0-gvdb-1';work=base/'phase2/work/dconf-vendored-1';receipt=log/'dconf-gvdb-input-1.json'
if finish:
 assert source.is_dir() and not work.exists() and json.loads(receipt.read_text())['state']=='copying'
else:assert not source.exists() and not work.exists() and not receipt.exists(),'Reconcile input before repeat'
assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+64*1024**2
assert 'revision='+extra['commit'] in (original/'subprojects/gvdb.wrap').read_text()
data=sys.stdin.buffer.read();assert hashlib.sha256(data).hexdigest()==extra['sha256']
archive=base/extra['filename'];part=archive.with_name(archive.name+'.part');assert not part.exists()
if archive.exists():assert hashlib.sha256(archive.read_bytes()).hexdigest()==extra['sha256']
else:
 with part.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 part.rename(archive)
def inventory(base):
 return {str(p.relative_to(base)):(('link',str(p.readlink())) if p.is_symlink() else ('sha256',hashlib.sha256(p.read_bytes()).hexdigest())) for p in base.rglob('*') if p.is_symlink() or p.is_file()}
state={'state':'copying','source':str(source),'work':str(work),'extra_source':extra,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':os.getpid(),'started_unix':time.time()}
def save():
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(state,f,indent=2);f.write('\\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
before=inventory(original)
if not finish:save();shutil.copytree(original,source,symlinks=True);assert inventory(source)==before
expected={}
with tarfile.open(archive) as t:
 for m in t:
  rel=Path(m.name).relative_to('gvdb-'+extra['commit'])
  assert not rel.is_absolute() and '..' not in rel.parts
  if m.isfile():expected[str(rel)]=('sha256',hashlib.sha256(t.extractfile(m).read()).hexdigest())
  elif m.issym():expected[str(rel)]=('link',m.linkname)
  else:assert m.isdir()
assert len(expected)==15 and inventory(original/'subprojects/gvdb')==inventory(source/'subprojects/gvdb')==expected
if finish:
 duplicate=source/'subprojects'/('gvdb-'+extra['commit']);assert duplicate.resolve()==duplicate and duplicate.is_dir() and not duplicate.is_symlink() and inventory(duplicate)==expected
 actual=inventory(source);prefix=str(duplicate.relative_to(source))+'/'
 assert {k:v for k,v in actual.items() if not k.startswith(prefix)}==before
 state.update(state='finishing-verified-copy',bundled_gvdb_files=len(expected));save()
 shutil.rmtree(duplicate);assert not duplicate.exists()
assert inventory(source)==before
(source/'toddy-build.sh').write_text(recipe)
prepared=json.loads((source/'toddy-prepared.json').read_text());prepared.update(extra_source=extra,recipe_sha256=hashlib.sha256(recipe.encode()).hexdigest())
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\\n')
assert inventory(original)==before
work.mkdir();os.chown(work,101,101)
state.update(state='complete',original_files_unchanged=len(before),recipe_sha256=hashlib.sha256(recipe.encode()).hexdigest());save();print(json.dumps(state))
'''
    compile(code,'dconf-gvdb-input','exec')
    subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],input=archive,check=True)
if __name__=='__main__':main()
