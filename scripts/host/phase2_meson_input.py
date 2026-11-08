#!/usr/bin/env python3
"""Prepare a selected immutable source/recipe input, never install it."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import phase2_vm
ROOT=phase2_vm.ROOT
NAME=sys.argv[1]
assert NAME in ('wayland','wayland-protocols','pixman','libpng','freetype','fontconfig','fribidi')
if __name__=='__main__':
    row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==NAME)
    archive=ROOT/'.local/sources'/row['filename'];data=archive.read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    probe=(ROOT/'scripts/build/phase2/freetype-probe.c').read_text() if NAME=='freetype' else None
    recipe=(ROOT/'scripts/build/phase2'/(NAME+'-build.sh')).read_text()
    remote='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={row!r}\nrecipe={recipe!r}\nprobe={probe!r}\n'+'''
base=Path('/mnt/lfs/sources');archive=base/row['filename'];part=base/(row['filename']+'.part')
source=base/'phase2/inputs'/(row['name']+'-'+row['version']);work=base/'phase2/work'/(row['name']+'-1')
assert not source.exists() and not work.exists() and not part.exists(),'Reconcile existing source/job; no replay'
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
patches=[]
if row['name']=='freetype':
    import re
    for relative in ['modules.cfg','include/freetype/config/ftoption.h']:
        path=source/relative;before=path.read_bytes();text=before.decode()
        if relative=='modules.cfg':
            text,count=re.subn(r'^# (AUX_MODULES [+]= (?:gxvalid|otvalid))$',lambda match:match.group(1),text,flags=re.M);assert count==2
        else:
            old='/* #define FT_CONFIG_OPTION_SUBPIXEL_RENDERING */'
            assert text.count(old)==1;text=text.replace(old,'#define FT_CONFIG_OPTION_SUBPIXEL_RENDERING')
        path.write_text(text)
        patches.append({'path':relative,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reference':'BLFS13.1 general/freetype2.html'})
(source/'toddy-build.sh').write_text(recipe)
receipt={'source_sha256':row['sha256'],'reference':row['reference'],
         'book_page_sha256':row['book_page_sha256'],'source_patches':patches,
         'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()}
if probe is not None:
    (source/'toddy-probe.c').write_text(probe)
    receipt['probe_sha256']=hashlib.sha256(probe.encode()).hexdigest()
(source/'toddy-prepared.json').write_text(json.dumps(receipt,indent=2)+'\\n')
work.mkdir();os.chown(work,101,101)
print(json.dumps(receipt))
'''
    prefix=ROOT/'.local/phase2'/(NAME+'-input')
    with prefix.with_suffix('.log').open('xb') as log:
        result=subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(remote)],input=data,stdout=log,stderr=subprocess.STDOUT)
    prefix.with_suffix('.exit').write_text(str(result.returncode)+'\n')
    raise SystemExit(result.returncode)
