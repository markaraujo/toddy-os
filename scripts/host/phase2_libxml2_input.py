#!/usr/bin/env python3
"""Prepare one exact XML input/job, reusing verified guest sources on resumption."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import phase2_vm
ROOT=phase2_vm.ROOT
if __name__=='__main__':
    row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']=='libxml2')
    archive=ROOT/'.local/sources'/row['filename']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==row['sha256']
    recipe=(ROOT/'scripts/build/phase2/libxml2-build.sh').read_text()
    remote='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={row!r}\nrecipe={recipe!r}\n'+'''
base=Path('/mnt/lfs/sources');archive=base/row['filename'];part=base/(row['filename']+'.part')
source=base/'phase2/inputs/libxml2-2.15.3';work=base/'phase2/work/libxml2-1'
assert not source.exists() and not work.exists() and not part.exists(), 'Reconcile existing input/work; no replay'
if archive.exists():
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==row['sha256']
    assert hashlib.sha256(sys.stdin.buffer.read()).hexdigest()==row['sha256']
else:
    digest=hashlib.sha256()
    with part.open('xb') as output:
        while chunk:=sys.stdin.buffer.read(1024*1024):output.write(chunk);digest.update(chunk)
        output.flush();os.fsync(output.fileno())
    assert digest.hexdigest()==row['sha256'];part.rename(archive)
assert os.statvfs(base).f_bavail*os.statvfs(base).f_frsize>=16*1024**3
subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',row['filename']],cwd=base/'phase2/inputs',check=True)
meson=source/'meson.build';text=meson.read_text()
block="r = run_command('git', 'describe', check: false)\\nif (r.returncode() == 0)\\n    v_extra = '-GIT' + r.stdout().strip()\\nendif\\n"
assert text.count(block)==1,'Exact frozen BLFS git-describe correction'
meson.write_text(text.replace(block,''))
(source/'toddy-build.sh').write_text(recipe)
receipt={'source_sha256':row['sha256'],'book_reference':'BLFS13.1 general/libxml2.html',
         'patch':'Exact four-line git-describe removal from frozen book; no native Git requirement at this bootstrap',
         'prepared_meson_sha256':hashlib.sha256(meson.read_bytes()).hexdigest(),
         'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()}
(source/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+'\\n')
work.mkdir();os.chown(work,101,101)
print(json.dumps(receipt))
'''
    with (ROOT/'.local/phase2/libxml2-input.log').open('xb') as log:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=archive.read_bytes(),stdout=log,stderr=subprocess.STDOUT)
    (ROOT/'.local/phase2/libxml2-input.exit').write_text(str(result.returncode)+'\n')
    raise SystemExit(result.returncode)
