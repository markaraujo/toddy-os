#!/usr/bin/env python3
"""Authenticate and prepare frozen security-backported PAM in the builder only."""
import hashlib,json,shlex,shutil,subprocess
from pathlib import Path
import phase2_vm
ROOT=phase2_vm.ROOT

def main():
    assert shutil.disk_usage(ROOT).free>=100*1024**3
    row=next(x for x in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if x['name']=='linux-pam')
    lock=json.loads((ROOT/'config/phase2/pam-patches.lock.json').read_text())
    expected=json.loads((ROOT/'docs/evidence/B02-pam-source-preparation.json').read_text())['changed_source_files']
    assert row['version']=='1.7.2' and row['sha256']==lock['source_sha256']
    data=(ROOT/'.local/sources'/row['filename']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
    patches=[]
    for r in lock['patches']:
        text=(ROOT/r['file']).read_text();assert hashlib.sha256(text.encode()).hexdigest()==r['sha256'];patches.append((r,text))
    files={n:(ROOT/'scripts/build/phase2'/c).read_text() for n,c in [('toddy-build.sh','pam-build.sh'),('toddy-probe.c','pam-probe.c')]}
    code=r'''from pathlib import Path
import fcntl,hashlib,json,os,shutil,socket,subprocess,sys,time
assert os.geteuid()==0 and socket.gethostname()=='toddy-builder'
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lockfd=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lockfd,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={row!r}\npatches={patches!r}\nexpected={expected!r}\nfiles={files!r}\n'+r'''
source=Path('/mnt/lfs/sources/phase2/inputs/linux-pam-1.7.2-security-1');work=Path('/mnt/lfs/sources/phase2/work/pam-1')
receipt=Path('/var/log/toddy/phase2/pam-input-1.json')
assert not source.exists() and not receipt.exists(),'Reconcile prior input, never replay'
assert work.is_dir() and work.stat().st_uid==101
mount=json.loads(Path('/var/log/toddy/phase2/pam-build-volume.json').read_text());assert mount['state']=='mounted'
assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(work)],text=True).strip()==mount['filesystem_uuid']
assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+32*1024**2
state={'state':'preparing','source':str(source),'work':str(work),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':os.getpid(),'started_unix':time.time()}
def save():
 part=receipt.with_suffix('.part');assert not part.exists()
 with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 part.replace(receipt)
data=sys.stdin.buffer.read();assert hashlib.sha256(data).hexdigest()==row['sha256']
archive=Path('/mnt/lfs/sources')/row['filename']
if archive.exists():assert hashlib.sha256(archive.read_bytes()).hexdigest()==row['sha256']
else:
 with archive.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
save();source.mkdir()
subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['filename']],cwd=source,check=True,stdout=subprocess.DEVNULL)
inner=source/'Linux-PAM-1.7.2';assert inner.is_dir()
for p in list(inner.iterdir()):p.rename(source/p.name)
inner.rmdir()
patchlog=Path('/var/log/toddy/phase2/pam-input-patches.log')
with patchlog.open('x') as log:
 for r,text in patches:
  assert hashlib.sha256(text.encode()).hexdigest()==r['sha256']
  subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1'],cwd=source,input=text,text=True,stdout=log,stderr=subprocess.STDOUT,check=True)
for name,sha in expected.items():assert hashlib.sha256((source/name).read_bytes()).hexdigest()==sha
for name,text in files.items():(source/name).write_text(text)
prepared={'source_sha256':row['sha256'],'source_patches':[r for r,_ in patches],'changed_source_files':expected,'recipe_sha256':hashlib.sha256(files['toddy-build.sh'].encode()).hexdigest(),'probe_sha256':hashlib.sha256(files['toddy-probe.c'].encode()).hexdigest(),'scratch_uuid':mount['filesystem_uuid']}
(source/'toddy-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
state.update(state='complete',prepared=prepared);save();print(json.dumps({'state':'complete','source':str(source),'patched_files':len(expected),'patches':len(patches)}))
'''
    compile(code,'pam-input','exec')
    subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],input=data,check=True)

if __name__=='__main__':main()
