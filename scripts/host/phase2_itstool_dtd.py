#!/usr/bin/env python3
"""Prepare immutable itstool+offline DocBook input without changing old inputs."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import phase2_vm


def main():
    row=next(r for r in json.loads((phase2_vm.ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='docbook-xml')
    data=(phase2_vm.ROOT/'.local/sources'/row['filename']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    code='''from pathlib import Path
import fcntl,hashlib,json,os,shutil,stat,subprocess,sys,zipfile
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
l=open('/var/log/toddy/build/build.lock','a');fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={row!r}\n'+'''
base=Path('/mnt/lfs/sources');old=base/'phase2/inputs/itstool-2.0.7';new=base/'phase2/inputs/itstool-dtd-4.5'
assert old.is_dir() and not new.exists()
fs=os.statvfs(base);assert fs.f_bavail*fs.f_frsize>16*1024**3+64*1024**2
archive=base/row['filename'];part=archive.with_suffix('.zip.part');assert not archive.exists() and not part.exists()
data=sys.stdin.buffer.read();assert hashlib.sha256(data).hexdigest()==row['sha256']
with part.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
with zipfile.ZipFile(part) as z:
 assert z.testzip() is None
 for m in z.infolist():
  p=Path(m.filename);assert not p.is_absolute() and '..' not in p.parts and not stat.S_ISLNK(m.external_attr>>16)
part.rename(archive);shutil.copytree(old,new,symlinks=True);dtd=new/'docbook';dtd.mkdir()
with zipfile.ZipFile(archive) as z:
 for m in z.infolist():
  p=dtd/m.filename
  if m.is_dir():p.mkdir(parents=True,exist_ok=True)
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(m));p.chmod(0o644)
receipt={'scope':'Readonly supplemental offline DocBook fixture; no runtime install','source':row,'parent_prepared':json.loads((old/'toddy-prepared.json').read_text()),'members':len(z.infolist())}
(new/'toddy-dtd-prepared.json').write_text(json.dumps(receipt,indent=2)+'\\n')
print(json.dumps(receipt))
'''
    subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(code)],input=data,check=True)


if __name__=='__main__':main()
