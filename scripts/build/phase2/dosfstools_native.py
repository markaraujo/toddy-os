"""Frozen dosfstools4.2 native pipeline; the coordinator is the sole guest writer."""
import argparse
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
from dosfstools_inspect import layout,tests
from verify_stage import inspect_stage
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
SOURCE=TARGET/'sources/phase2/inputs/dosfstools-4.2-1';HOLDER=TARGET/'sources/phase2/holders/dosfstools-4.2-1'
WORK=TARGET/'sources/phase2/work/dosfstools-1';STAGE=TARGET/'sources/stage/phase2-dosfstools-1'
PREPARED=LOG/'dosfstools-prepared-1.json';ACCEPTED=LOG/'dosfstools-qualified-1.json'
ARCHIVE='dosfstools-4.2.tar.gz';SHA='64926eebf90092dca21b14259a5301b7b98e7b1943e8a201c7d726084809b527'
MD5='49c8e457327dc61efab5b115a27b087a';VERSION='4.2-1+toddy1';DEPENDS='glibc (>= 2.44-1)'
STEP='b12-dosfstools-install-1';INSTALL='scripts/build/phase2/dosfstools-install.sh';CHECK='scripts/build/phase2/dosfstools-check.sh'
SCRIPTS={'toddy-build.sh':'dosfstools-build.sh','toddy-file-probe.py':'dosfstools_file_probe.py','toddy-inspect.py':'dosfstools_inspect.py','verify_stage.py':'verify_stage.py'}


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):
    part=path.with_suffix('.part')
    with part.open('x') as stream:json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    part.replace(path)
    fd=os.open(path.parent,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def native(*args):return subprocess.check_output(['chroot',str(TARGET),'/usr/bin/env','-i','HOME=/root','PATH=/usr/bin:/usr/sbin','LC_ALL=C',*args],text=True).strip()


def source_row():
    from locked_inputs import locked_source
    row=locked_source(ROOT,ARCHIVE)
    if not row or row['name']!='dosfstools' or row['version']!='4.2' or row['sha256']!=SHA or row.get('status')!='source_verified':raise ValueError('Parent-verified frozen dosfstools source row required')
    archive=TARGET/'sources'/ARCHIVE
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size!=320917 or digest(archive)!=SHA or hashlib.md5(archive.read_bytes(),usedforsecurity=False).hexdigest()!=MD5:raise ValueError('Frozen dosfstools source bytes differ')
    return row


def dependencies():
    state={}
    for name in ('glibc','vim'):
        status,version=native('dpkg-query','-W','-f=${Status}\t${Version}',name).split('\t')
        if status!='install ok installed':raise ValueError('Native build/provider dependency absent: '+name)
        record=Path('/var/log/toddy/packages')/(name+'_'+version+'_amd64.json');value=json.loads(record.read_bytes())
        archive=Path('/var/cache/toddy/packages')/(name+'_'+version+'_amd64.deb')
        if value.get('installed') is not True or digest(archive)!=value['archive_sha256']:raise ValueError('Native dependency custody differs')
        state[name]={'version':version,'record_sha256':digest(record),'archive_sha256':value['archive_sha256']}
    xxd=TARGET/'usr/bin/xxd';record=json.loads((Path('/var/log/toddy/packages')/('vim_'+state['vim']['version']+'_amd64.json')).read_bytes())
    if xxd.is_symlink() or not xxd.is_file() or record['payload'].get('/usr/bin/xxd',{}).get('sha256')!=digest(xxd):raise ValueError('Actual owned native xxd required; no skipped tests')
    return state


def reserve(extra=0):
    if shutil.disk_usage(TARGET).free<16*1024**3+512*1024**2+extra:raise ValueError('Preserve16GiB target reserve plus512MiB scratch')


def pins():
    names=[*SCRIPTS.values(),'dosfstools_native.py','job.py','isolated.sh']
    return {name:digest(HERE/name) for name in sorted(names)}


def prepare():
    from source_filter import source_filter,validate_source_members
    source_row();state=dependencies();reserve()
    if native('id','-u','tester')!='101' or native('id','-g','tester')!='101':raise ValueError('Qualified fixed native tester required')
    if subprocess.run(['chroot',str(TARGET),'dpkg-query','-W','dosfstools'],capture_output=True).returncode!=1:raise ValueError('First native dosfstools package must be absent')
    for path in (SOURCE,HOLDER,WORK,STAGE,PREPARED,ACCEPTED,PREPARED.with_suffix('.part')):
        if os.path.lexists(path):raise ValueError('Existing dosfstools state; inspect before any replay')
    source_parent=SOURCE.parent;source_parent.mkdir(parents=True,exist_ok=True);HOLDER.parent.mkdir(parents=True,exist_ok=True);WORK.parent.mkdir(parents=True,exist_ok=True)
    state={'state':'prepare-intended','source_sha256':SHA,'dependencies':state,'scripts':pins(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()};save(PREPARED,state)
    HOLDER.mkdir(mode=0o755)
    with tarfile.open(TARGET/'sources'/ARCHIVE) as bundle:
        members=bundle.getmembers()
        if len(members)!=157 or sum(m.size for m in members if m.isfile())!=1356148 or any(Path(m.name).parts[0]!='dosfstools-4.2' or m.issym() or m.islnk() for m in members):raise ValueError('Frozen dosfstools archive members differ')
        validate_source_members(ARCHIVE,members);checked=source_filter(ARCHIVE)
        for member in members:checked(member,HOLDER)
        bundle.extractall(HOLDER,filter=checked)
    tree=HOLDER/'dosfstools-4.2'
    for name,filename in SCRIPTS.items():
        if os.path.lexists(tree/name):raise ValueError('Unexpected injected build source')
        (tree/name).write_bytes((HERE/filename).read_bytes());(tree/name).chmod(0o644)
    SOURCE.mkdir(mode=0o755);subprocess.run(['mount','--bind',str(tree),str(SOURCE)],check=True);subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(SOURCE)],check=True)
    try:fd=os.open(SOURCE/'.toddy-denial',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except OSError as error:
        if error.errno!=errno.EROFS:raise
    else:os.close(fd);raise ValueError('Root source write unexpectedly permitted')
    WORK.mkdir(mode=0o755);os.chown(WORK,101,101)
    state.update(state='prepared',root_source_write_denied=True,source_inode=SOURCE.stat().st_ino,work_inode=WORK.stat().st_ino);save(PREPARED,state)


def elf_dependencies(stage,expected):
    from audit_native_elf import target_resolve
    version=expected['glibc']['version'];record=json.loads((Path('/var/log/toddy/packages')/('glibc_'+version+'_amd64.json')).read_bytes());checked=[]
    for name in ('fsck.fat','mkfs.fat','fatlabel'):
        path=stage/'usr/sbin'/name;dynamic=subprocess.check_output(['readelf','-d',str(path)],text=True);libraries=[]
        for kind,value in re.findall(r'\((NEEDED|RPATH|RUNPATH)\).*\[(.*?)\]',dynamic):
            if kind!='NEEDED' or '/' in value or not value:raise ValueError('Unexpected dosfstools ELF runtime path')
            provider,canonical=target_resolve(TARGET,'/usr/lib/'+value)
            if not provider.is_file() or record['payload'].get(canonical,{}).get('sha256')!=digest(provider):raise ValueError('Undeclared/noncanonical dosfstools ELF provider')
            libraries.append({'soname':value,'owner':'glibc','path':canonical,'sha256':digest(provider)})
        header=subprocess.check_output(['readelf','-h',str(path)],text=True)
        if 'ELF64' not in header or 'Advanced Micro Devices X86-64' not in header or not libraries:raise ValueError('Actual native AMD64 dynamic executable required')
        program=subprocess.check_output(['readelf','-l',str(path)],text=True)
        interpreter=re.findall(r'Requesting program interpreter: ([^\]]+)',program)
        if interpreter!=['/lib64/ld-linux-x86-64.so.2']:raise ValueError('Native ELF interpreter differs')
        loader,canonical=target_resolve(TARGET,interpreter[0])
        if not loader.is_file() or record['payload'].get(canonical,{}).get('sha256')!=digest(loader):raise ValueError('Native ELF loader custody differs')
        checked.append({'path':'/usr/sbin/'+name,'providers':libraries,'interpreter':interpreter[0],'loader_sha256':digest(loader),'sha256':digest(path)})
    return checked


def qualified():
    state=json.loads(PREPARED.read_bytes())
    if state['state']!='prepared' or state['scripts']!=pins() or state['dependencies']!=dependencies() or state['boot_id']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip() or SOURCE.stat().st_ino!=state['source_inode'] or WORK.stat().st_ino!=state['work_inode']:raise ValueError('Prepared native inputs changed')
    source_row()
    for name,filename in SCRIPTS.items():
        if digest(SOURCE/name)!=state['scripts'][filename]:raise ValueError('Readonly source script pin differs')
    job=json.loads((LOG/'dosfstools-1.job.json').read_bytes())
    command=['/bin/bash',str(HERE/'isolated.sh'),str(SOURCE),str(WORK),'bash','/src/toddy-build.sh']
    if job['command']!=command or job['harness_sha256']!=state['scripts']['isolated.sh'] or (LOG/'dosfstools-1.exit').read_text().strip()!='0' or (WORK/'original-tests.exit').read_text().strip()!='0':raise ValueError('Actual successful isolated native build/test exit required')
    results=tests(WORK/'compile/tests',SOURCE/'tests/Makefile.am')
    if results!=json.loads((WORK/'original-tests.json').read_bytes()):raise ValueError('Actual upstream results differ')
    stage=inspect_stage(WORK/'stage')
    if stage!=json.loads((WORK/'stage-results.json').read_bytes()):raise ValueError('Native stage changed')
    proof=json.loads((WORK/'fat32-file-probe.json').read_bytes())
    if proof['uid']!=101 or proof['regular_file_only'] is not True or proof['raw_or_loop_device_used'] is not False or proof['logical_bytes']!=128*1024**2 or any(proof[key]!=0 for key in ('mkfs_exit','fsck_exit','fatlabel_exit')) or proof['readonly_check_preserved_bytes'] is not True:raise ValueError('Actual regular-file FAT32 consumer required')
    source_doc=SOURCE/'COPYING';staged_doc=WORK/'stage/usr/share/doc/dosfstools-4.2/COPYING'
    if digest(source_doc)!=digest(staged_doc):raise ValueError('Upstream legal notice changed')
    return {'version':VERSION,'source_sha256':SHA,'stage':stage,'layout':layout(WORK/'stage'),'elfs':elf_dependencies(WORK/'stage',state['dependencies']),'upstream_tests':results,'file_probe':proof,'dependencies':state['dependencies'],'scripts':state['scripts']}


def qualify():
    reserve();proof=qualified()
    if ACCEPTED.exists():raise ValueError('Keep prior qualification receipt; no replay')
    save(ACCEPTED,proof)


def transaction(action):
    value=json.loads((LOG.parent/'build'/(STEP+'.running.json')).read_bytes())
    if value['step']!=STEP or value['user']!='root' or value['recipe_sha256']!=digest(ROOT/INSTALL) or value['postcheck_sha256']!=digest(ROOT/CHECK):raise ValueError('Pinned full-root run_step transaction required')
    if action=='install':
        if value['recipe_pid'] not in (os.getpid(),os.getppid()):raise ValueError('Native install parent differs')
    elif value['recipe_exit']!=0:raise ValueError('Successful native recipe exit required')


def install():
    from package_copyright import write_copyright
    from dependency_preflight import native as verify_dependencies
    transaction('install');proof=qualified()
    if proof!=json.loads(ACCEPTED.read_bytes()):raise ValueError('Qualified native stage receipt differs')
    verify_dependencies(DEPENDS);extra=sum(max(4096,p.lstat().st_size) for p in (WORK/'stage').rglob('*'));reserve(3*extra)
    if os.path.lexists(STAGE):raise ValueError('Preserve prior promotion stage')
    if subprocess.run(['chroot',str(TARGET),'dpkg-query','-W','dosfstools'],capture_output=True).returncode!=1:raise ValueError('Only first native dosfstools install is authorized here')
    shutil.copytree(WORK/'stage',STAGE,symlinks=True)
    if inspect_stage(STAGE)!=proof['stage']:raise ValueError('Promotion copy differs')
    for path in [STAGE,*STAGE.rglob('*')]:os.chown(path,0,0,follow_symlinks=False)
    write_copyright(STAGE,'dosfstools',[ARCHIVE])
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'dosfstools',VERSION,str(STAGE),'--recipe',INSTALL,'--source',ARCHIVE,'--depends',DEPENDS,'--install'],cwd=ROOT,check=True)
    save(LOG/'dosfstools-installed-1.json',{'version':VERSION,'native_record_sha256':digest(Path('/var/log/toddy/packages')/('dosfstools_'+VERSION+'_amd64.json')),'qualified_receipt_sha256':digest(ACCEPTED),'stage_manifest_sha256':inspect_stage(STAGE)['manifest_sha256'],'source_sha256':SHA})


def check():
    transaction('check')
    if native('dpkg-query','-W','-f=${Status} ${Version}','dosfstools')!='install ok installed '+VERSION:raise ValueError('Actual configured native dosfstools version required')
    record_path=Path('/var/log/toddy/packages')/('dosfstools_'+VERSION+'_amd64.json');record=json.loads(record_path.read_bytes())
    if record['installed'] is not True or record['sources'][0]['sha256']!=SHA or digest(Path('/var/cache/toddy/packages')/('dosfstools_'+VERSION+'_amd64.deb'))!=record['archive_sha256']:raise ValueError('Native source/archive package custody differs')
    receipt=json.loads((LOG/'dosfstools-installed-1.json').read_bytes())
    if inspect_stage(STAGE)['manifest_sha256']!=receipt['stage_manifest_sha256'] or digest(ACCEPTED)!=receipt['qualified_receipt_sha256']:raise ValueError('Promoted stage/receipt changed')
    if receipt['native_record_sha256']!=digest(record_path) or record['recipe_sha256']!=digest(ROOT/INSTALL):raise ValueError('Native package record/recipe changed')
    checked=[]
    for virtual,row in record['payload'].items():
        if row.get('directory'):continue
        path=TARGET/virtual.lstrip('/');info=path.lstat()
        if info.st_uid!=row['uid'] or info.st_gid!=row['gid'] or info.st_mode!=row['mode']:raise ValueError('Installed native mode/owner differs')
        if 'symlink' in row:
            if not path.is_symlink() or str(path.readlink())!=row['symlink']:raise ValueError('Installed compatibility link differs')
        elif not path.is_file() or path.is_symlink() or digest(path)!=row['sha256']:raise ValueError('Installed native bytes differ')
        if native('dpkg-query','-S',virtual)!='dosfstools: '+virtual:raise ValueError('Installed ownership differs')
        checked.append(virtual)
    layout(TARGET);elf_dependencies(STAGE,json.loads(ACCEPTED.read_bytes())['dependencies'])
    with tempfile.TemporaryDirectory(prefix='toddy-fat32-',dir=TARGET/'var/tmp') as temporary:
        directory=Path(temporary);os.chown(directory,101,101)
        script=directory/'probe.py';script.write_bytes((HERE/'dosfstools_file_probe.py').read_bytes());script.chmod(0o644)
        virtual='/var/tmp/'+directory.name
        result=subprocess.run(['setpriv','--no-new-privs','chroot','--userspec=101:101','--groups=101',str(TARGET),'/usr/bin/python3','-I','-B',virtual+'/probe.py','--tools','/usr/sbin','--directory',virtual],capture_output=True,text=True,timeout=60)
        if result.returncode!=0:raise ValueError('Actual installed regular-file FAT32 probe failed: '+result.stderr)
        consumer=json.loads(result.stdout)
    if native('dpkg','--audit'):raise ValueError('Native package audit failure')
    native('apt-get','check');reserve()
    save(LOG/'dosfstools-checked-1.json',{'version':VERSION,'record_sha256':digest(record_path),'checked':checked,'installed_file_probe':consumer,'scope':'Actual native package/regular sparse FAT32 file only; raw disk/installer boot remains separate'})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','qualify','install','check']);args=parser.parse_args()
    if os.getuid()!=0 or os.geteuid()!=0:raise ValueError('Guarded disposable native builder root required')
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    os.umask(0o022)
    if args.action in ('prepare','qualify'):
        with (LOG.parent/'build/build.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if list((LOG.parent/'build').glob('*.running.json')):raise ValueError('Reconcile existing native writer first')
            globals()[args.action]()
    else:globals()[args.action]() # Existing run_step already holds the lock.


if __name__=='__main__':main()
