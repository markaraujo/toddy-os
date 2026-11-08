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
assert NAME in ('wayland','wayland-protocols','pixman','libpng','freetype','fontconfig','fribidi','harfbuzz','cairo','pango','graphene','shared-mime-info','llvm','adwaita-fonts','dejavu-fonts','libjpeg-turbo','psutil','mako')
if __name__=='__main__':
    row=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==NAME)
    archive=ROOT/'.local/sources'/row['filename'];data=archive.read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256']
    probes={'freetype':'freetype-probe.c','psutil':'psutil-probe.py','mako':'mako-probe.py'}
    probe=(ROOT/'scripts/build/phase2'/probes[NAME]).read_text() if NAME in probes else None
    extra=None
    if NAME in ('shared-mime-info','llvm'):
        extra_name='xdgmime-tests' if NAME=='shared-mime-info' else 'llvm-upstream-fix'
        extra=next(r for r in json.loads((ROOT/'config/phase2/sources.lock.json').read_text())['components'] if r['name']==extra_name)
        extra_data=(ROOT/'.local/sources'/extra['filename']).read_bytes()
        assert hashlib.sha256(extra_data).hexdigest()==extra['sha256']
        transfer='''from pathlib import Path
import fcntl,hashlib,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={extra!r}\n'+'''
p=Path('/mnt/lfs/sources')/row['filename'];part=p.with_name(p.name+'.part')
assert not part.exists(),'Reconcile partial test-source transfer'
data=sys.stdin.buffer.read();assert hashlib.sha256(data).hexdigest()==row['sha256']
if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
else:
 with part.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 part.rename(p)
'''
        subprocess.run(phase2_vm.ssh_args()+['python3 -c '+shlex.quote(transfer)],input=extra_data,check=True)
    recipe=(ROOT/'scripts/build/phase2'/(NAME+'-build.sh')).read_text()
    remote='''from pathlib import Path
import fcntl,hashlib,json,os,subprocess,sys
subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
'''+f'row={row!r}\nrecipe={recipe!r}\nprobe={probe!r}\nextra={extra!r}\n'+'''
base=Path('/mnt/lfs/sources');archive=base/row['filename'];part=base/(row['filename']+'.part')
source_name='llvm-project-'+row['version']+'.src' if row['name']=='llvm' else 'dejavu-fonts-ttf-'+row['version'] if row['name']=='dejavu-fonts' else row['name']+'-'+row['version']
source=base/'phase2/inputs'/source_name;work=base/'phase2/work'/(row['name']+'-1')
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
if row['name']=='mako':
    import stat
    path=source/'doc/build/changelog.rst';before=stat.S_IMODE(path.stat().st_mode)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    assert before==0o600 and sha=='a5620499d6c083972b0ba7ea307b99b06e783966fa46b3e5c73d00fe96f51e31'
    path.chmod(0o644)
    patches.append({'path':'doc/build/changelog.rst','before_mode':before,'after_mode':0o644,
                    'content_sha256':sha,'reason':'Public release doc is owner-readable only; expose unchanged bytes to unprivileged read-only-input compiler'})
if row['name']=='shared-mime-info':
    assert extra['name']=='xdgmime-tests'
    subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',extra['filename']],cwd=source/'subprojects',check=True)
    (source/'subprojects'/('xdgmime-'+extra['commit'])).rename(source/'subprojects/xdgmime')
    path=source/'tests/meson.build';before=path.read_bytes();text=before.decode()
    old="args: meson.current_source_dir() / 'mime-db-tests',";assert text.count(old)==1
    text=text.replace(old,"args: '/build/mime-db-tests',");path.write_text(text)
    patches.append({'path':'tests/meson.build','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reason':'Writable generated MIME cache test fixture under private /build; expected XML/tests unchanged'})
if row['name']=='llvm':
    import re
    assert extra['name']=='llvm-upstream-fix'
    subprocess.run(['python3','/opt/toddy-build/scripts/build/source.py',extra['filename'],'--verify-only'],check=True)
    patch_path=base/extra['filename'];body=patch_path.read_text()
    paths=re.findall(r'^[+][+][+] b/(.+)$',body,re.M)
    assert len(paths)==14 and all(p.startswith('llvm/') and '..' not in Path(p).parts for p in paths)
    before={p:hashlib.sha256((source/p).read_bytes()).hexdigest() if (source/p).exists() else None for p in paths}
    subprocess.run(['patch','--batch','--forward','--fuzz=0','-Np1','-i',str(patch_path)],cwd=source,check=True)
    patches.extend({'path':p,'before_sha256':before[p],'after_sha256':hashlib.sha256((source/p).read_bytes()).hexdigest(),'patch_sha256':extra['sha256']} for p in paths)
    path=source/'llvm/utils/FileCheck/CMakeLists.txt';data=path.read_bytes();text=data.decode();assert text.count('utility')==1
    path.write_text(text.replace('utility','tool'))
    patches.append({'path':'llvm/utils/FileCheck/CMakeLists.txt','before_sha256':hashlib.sha256(data).hexdigest(),'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reference':'BLFS13.1 install required FileCheck tool'})
    for path in source.rglob('*'):
        if not path.is_file() or path.is_symlink():continue
        with path.open('rb') as f:first=f.readline(4096)
        if re.fullmatch(rb'#![^\\n]*python\\r?\\n',first):
            before=path.read_bytes();after=first.rstrip().removesuffix(b'python')+b'python3\\n'+before[len(first):];path.write_bytes(after)
            patches.append({'path':str(path.relative_to(source)),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'reference':'BLFS13.1 Python3 shebang selection'})
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
         'book_page_sha256':row.get('book_page_sha256'),'source_patches':patches,
         'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()}
if extra is not None:receipt['extra_source']=extra
if probe is not None:
    (source/('toddy-probe.py' if row['name'] in ('psutil','mako') else 'toddy-probe.c')).write_text(probe)
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
