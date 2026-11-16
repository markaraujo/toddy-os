#!/usr/bin/env python3
"""Installer revision4: current Python payload, exact qualified compile3 reuse."""
import fcntl,hashlib,importlib.util,json,os,shutil,stat,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import installer_native as frozen
import offline_payload as payload
ROOT=frozen.ROOT;TARGET=frozen.TARGET;LOG=frozen.LOG;BUILD=Path('/var/log/toddy/build')
GENERATION=4
VERSION='0.2.0-1+toddy2';STEP='b12-toddy-installer-4'
BASELINE_VERSION='0.2.0-1+toddy1'
SOURCE=TARGET/'sources/phase2/inputs/toddy-installer-0.2.0-4'
WORK=TARGET/'sources/phase2/work/toddy-installer-4';STAGE=TARGET/'sources/stage/phase2-toddy-installer-4'
PREPARED=LOG/'toddy-installer-prepared-4.json';RECEIPT=LOG/'toddy-installer-install-4.json'
POSTCHECK_HOME=TARGET/'tmp/toddy-installer-offscreen-postcheck-4'
INSTALL='scripts/build/phase2/installer_mvp_install.sh';CHECK='scripts/build/phase2/installer_mvp_check.sh'
OWN=('scripts/build/phase2/installer_mvp_native.py','scripts/build/phase2/installer_mvp_prepare.sh',INSTALL,CHECK)
REUSE_DOC='/usr/share/doc/toddy-installer/native-module-reuse-4.json'
MANIFEST='usr/share/doc/toddy-installer/source-manifest.json'

def configure(generation):
    global GENERATION,VERSION,STEP,BASELINE_VERSION,SOURCE,WORK,STAGE,PREPARED,RECEIPT,POSTCHECK_HOME,INSTALL,CHECK,OWN,REUSE_DOC
    if type(generation) is not int or generation not in (4,5):raise ValueError('Only fixed installer4 or installer5 generation')
    GENERATION=generation
    suffix='' if generation==4 else '5'
    VERSION='0.2.0-1+toddy2' if generation==4 else '0.2.0-1+toddy3'
    BASELINE_VERSION='0.2.0-1+toddy1' if generation==4 else '0.2.0-1+toddy2'
    STEP='b12-toddy-installer-'+str(generation)
    SOURCE=TARGET/('sources/phase2/inputs/toddy-installer-0.2.0-'+str(generation))
    WORK=TARGET/('sources/phase2/work/toddy-installer-'+str(generation));STAGE=TARGET/('sources/stage/phase2-toddy-installer-'+str(generation))
    PREPARED=LOG/('toddy-installer-prepared-'+str(generation)+'.json');RECEIPT=LOG/('toddy-installer-install-'+str(generation)+'.json')
    POSTCHECK_HOME=TARGET/('tmp/toddy-installer-offscreen-postcheck-'+str(generation))
    INSTALL='scripts/build/phase2/installer_mvp_install'+suffix+'.sh';CHECK='scripts/build/phase2/installer_mvp_check'+suffix+'.sh'
    OWN=('scripts/build/phase2/installer_mvp_native.py','scripts/build/phase2/installer_mvp_prepare'+suffix+'.sh',INSTALL,CHECK)
    REUSE_DOC='/usr/share/doc/toddy-installer/native-module-reuse-'+str(generation)+'.json'


def package(version=None):
    # Private generator instance: old source/version and prepared compile3 stay
    # immutable. The external producer's hash explicitly records this version.
    spec=importlib.util.spec_from_file_location('installer_revision4_package',ROOT/'scripts/build/phase2/installer_package.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);value.VERSION=VERSION if version is None else version;return value

def digest(path):return frozen.digest(path)
def read(path):return json.loads(Path(path).read_bytes())
def save(path,value):
    if path.exists():
        part=path.with_suffix('.part')
        with part.open('x') as stream:os.fchmod(stream.fileno(),0o600);json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(part,path)
    else:
        with path.open('x') as stream:os.fchmod(stream.fileno(),0o600);json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    fd=os.open(path.parent,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def original_compile():
    old=read(frozen.PREPARED);success=read(BUILD/(frozen.STEP+'.success.json'))
    if (old.get('state')!='prepared' or old.get('before')!=frozen.package_state() or old.get('harness_sha256')!=digest(ROOT/'scripts/build/phase2/isolated.sh') or
        frozen.SOURCE.stat().st_ino!=old.get('source_inode') or frozen.WORK.stat().st_ino!=old.get('work_inode')):raise ValueError('Installer3 qualified context changed')
    for relative,sha in old['inputs'].items():
        path=frozen.SOURCE/'repository'/relative
        if path.resolve()!=path or digest(path)!=sha:raise ValueError('Installer3 frozen source bytes changed')
    for name in frozen.package_module().COMPILE_INPUTS:
        relative='runtime/installer/calamares/'+name
        if digest(ROOT/relative)!=old['inputs'].get(relative):raise ValueError('Installer4 C++ input differs; explicit fresh compiler attempt required')
    if (success.get('step')!=frozen.STEP or type(success.get('recipe_exit')) is not int or success['recipe_exit']!=0 or
        type(success.get('postcheck_exit')) is not int or success['postcheck_exit']!=0 or
        success.get('recipe_sha256')!=old['inputs']['scripts/build/phase2/installer_install.sh'] or
        success.get('postcheck_sha256')!=old['inputs']['scripts/build/phase2/installer_check.sh']):raise ValueError('Actual Installer3 native success required')
    job=read(LOG/(frozen.JOB+'.job.json'))
    if (LOG/(frozen.JOB+'.exit')).read_text().strip()!='0' or job.get('harness_sha256')!=old['harness_sha256'] or job.get('command')!=['/bin/bash',str(ROOT/'scripts/build/phase2/isolated.sh'),str(frozen.SOURCE),str(frozen.WORK),'bash','/src/installer_build.sh']:raise ValueError('Actual isolated compile3 completion required')
    pkg=package('0.2.0-1+toddy1');module=frozen.WORK/'compile/libcalamares_viewmodule_toddy.so';receipt=frozen.WORK/'native-module-compile.json'
    binary,proof=pkg.validate_module(module,receipt,ROOT)
    # Independently reconstruct compile3's OLD source plan, never today's Python
    # payload. No code is imported/executed from the legacy cache ancestry.
    _,files,links=pkg.plan(frozen.SOURCE/'repository')
    files[pkg.MODULE]=(binary,0o644);files['/usr/share/doc/toddy-installer/native-module-compile.json']=(pkg.encoded(proof),0o644)
    oldmanifest=frozen.read_stage_manifest(frozen.WORK/'stage')
    expected={name:{'sha256':pkg.sha(data),'bytes':len(data),'mode':format(mode,'04o')} for name,(data,mode) in files.items()}
    if oldmanifest.get('files')!=expected or oldmanifest.get('dependency_links')!=links or oldmanifest.get('version')!='0.2.0-1+toddy1':raise ValueError('Compile3 original staged source plan changed')
    oldstage=frozen.inventory(frozen.WORK/'stage');frozen.elf_dependencies(frozen.WORK/'stage')
    own=read(frozen.RECEIPT)
    if own.get('state')!='native-installed-postcheck-pending' or own.get('stage_manifest_sha256')!=oldstage['manifest_sha256']:raise ValueError('Installer3 native receipt/stage binding changed')
    recordpath=Path('/var/log/toddy/packages/toddy-installer_0.2.0-1+toddy1_amd64.json');record=read(recordpath)
    archive=Path('/var/cache/toddy/packages/toddy-installer_0.2.0-1+toddy1_amd64.deb')
    control,actual,_=payload.archive_contents(archive)
    if (record.get('installed') is not True or record.get('recipe_sha256')!=old['inputs']['scripts/build/phase2/installer_install.sh'] or digest(archive)!=record.get('archive_sha256') or actual!=record.get('payload') or
        control.get('Package')!='toddy-installer' or control.get('Version')!='0.2.0-1+toddy1' or actual.get(pkg.MODULE,{}).get('sha256')!=hashlib.sha256(binary).hexdigest()):raise ValueError('Installer3 retained archive/record/module custody')
    return binary,proof,{'version':1,'scope':'actual-qualified-compile3-reuse-current-Python-repackage',
        'prepared3_sha256':digest(frozen.PREPARED),'job3_sha256':digest(LOG/(frozen.JOB+'.job.json')),'exit3_sha256':digest(LOG/(frozen.JOB+'.exit')),
        'success3_sha256':digest(BUILD/(frozen.STEP+'.success.json')),'manifest3_sha256':digest(BUILD/(frozen.STEP+'.manifest.json')),
        'native_receipt3_sha256':digest(frozen.RECEIPT),'old_record_sha256':digest(recordpath),'old_archive_sha256':digest(archive),
        'module_sha256':hashlib.sha256(binary).hexdigest(),'compile_receipt_sha256':digest(receipt),'native_dependencies':frozen.package_state(),
        'compile_inputs':proof['source_sha256'],'recompiled':False,'qt_calamares_rebuilt':False,'root_gui_qualified_by_repackage':False}


def upgrade4_baseline(check_installed=False):
    if GENERATION!=5:return None
    success_path=BUILD/'b12-toddy-installer-4.success.json';success=read(success_path)
    previous_prepared=LOG/'toddy-installer-prepared-4.json';prepared=read(previous_prepared)
    previous_receipt=LOG/'toddy-installer-install-4.json';receipt=read(previous_receipt)
    recordpath=Path('/var/log/toddy/packages/toddy-installer_0.2.0-1+toddy2_amd64.json');record=read(recordpath)
    archive=Path('/var/cache/toddy/packages/toddy-installer_0.2.0-1+toddy2_amd64.deb')
    if (success.get('step')!='b12-toddy-installer-4' or any(type(success.get(key)) is not int or success[key]!=0 for key in ('recipe_exit','postcheck_exit')) or
        success.get('recipe_sha256')!=digest(ROOT/'scripts/build/phase2/installer_mvp_install.sh') or success.get('postcheck_sha256')!=digest(ROOT/'scripts/build/phase2/installer_mvp_check.sh') or
        receipt.get('state')!='native-revision4-package-and-reused-plugin-verified' or receipt.get('prepared_sha256')!=digest(previous_prepared) or receipt.get('record_sha256')!=digest(recordpath) or
        receipt.get('archive_sha256')!=digest(archive) or prepared.get('state')!='prepared-reused-qualified-module'):
        raise ValueError('Installer5 requires actual preserved successful installer4')
    for name,sha in prepared['inputs'].items():
        path=TARGET/'sources/phase2/inputs/toddy-installer-0.2.0-4/repository'/name
        if path.resolve()!=path or digest(path)!=sha:raise ValueError('Preserved installer4 source changed')
    control,actual,_=payload.archive_contents(archive)
    if control.get('Version')!='0.2.0-1+toddy2' or actual!=record.get('payload') or digest(archive)!=record.get('archive_sha256'):raise ValueError('Installer4 retained archive/record changed')
    if check_installed:
        for name,row in actual.items():
            path=TARGET/name.lstrip('/');info=path.lstat()
            if info.st_mode!=row['mode'] or info.st_uid!=row['uid'] or info.st_gid!=row['gid'] or ('sha256' in row and digest(path)!=row['sha256']) or ('symlink' in row and os.readlink(path)!=row['symlink']):raise ValueError('Installer4 installed baseline differs')
    return {'step':'b12-toddy-installer-4','success_sha256':digest(success_path),'manifest_sha256':digest(BUILD/'b12-toddy-installer-4.manifest.json'),
        'prepared_sha256':digest(previous_prepared),'receipt_sha256':digest(previous_receipt),'record_sha256':digest(recordpath),'archive_sha256':digest(archive)}


def source_plan():
    pkg=package();inputs,files,links=pkg.plan(ROOT)
    for name in pkg.COMPILE_INPUTS:inputs['runtime/installer/calamares/'+name]=digest(ROOT/'runtime/installer/calamares'/name)
    inputs.update({name:digest(ROOT/name) for name in OWN})
    return inputs

def prepare():
    fresh=(SOURCE,WORK,STAGE,PREPARED,RECEIPT,POSTCHECK_HOME,PREPARED.with_suffix('.part'),RECEIPT.with_suffix('.part'),
        Path('/var/cache/toddy/packages')/('toddy-installer_'+VERSION+'_amd64.deb'),Path('/var/log/toddy/packages')/('toddy-installer_'+VERSION+'_amd64.json'))
    if any(os.path.lexists(path) for path in fresh):raise ValueError('Installer4 existing/uncertain preparation; no replay')
    if frozen.native('/usr/bin/dpkg-query','-W','-f=${Version}\t${Status}','toddy-installer')!=BASELINE_VERSION+'\tinstall ok installed':raise ValueError('Installer generation requires exact installed previous revision')
    binary,proof,reuse=original_compile();baseline=upgrade4_baseline(check_installed=True);inputs=source_plan()
    payload.require_capacity(TARGET,128*1024**2+3*sum((ROOT/name).stat().st_size for name in inputs))
    save(PREPARED,{'state':'preparing-no-replay','inputs':inputs,'reuse':reuse,'baseline_upgrade':baseline})
    SOURCE.mkdir(mode=0o755);(SOURCE/'repository').mkdir(mode=0o755);WORK.mkdir(mode=0o700)
    for name,sha in inputs.items():
        source=ROOT/name
        if source.resolve()!=source or digest(source)!=sha:raise ValueError('Installer4 source changed')
        target=SOURCE/'repository'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);target.chmod(0o444)
    for path in [*SOURCE.rglob('*'),SOURCE]:
        if path.is_dir():path.chmod(0o555)
    pkg=package();manifest=pkg.stage(ROOT,WORK/'stage',frozen.WORK/'compile/libcalamares_viewmodule_toddy.so',frozen.WORK/'native-module-compile.json')
    document=WORK/'stage'/REUSE_DOC.lstrip('/');document.write_bytes(pkg.encoded(dict(reuse,previous_package_upgrade=baseline) if baseline else reuse));document.chmod(0o644)
    manifest['inputs']=inputs;manifest['files'][REUSE_DOC]={'sha256':digest(document),'bytes':document.stat().st_size,'mode':'0644'}
    (WORK/'stage'/MANIFEST).write_bytes(pkg.encoded(manifest));(WORK/'stage'/MANIFEST).chmod(0o644)
    for path in [* (WORK/'stage').rglob('*'),WORK/'stage']:os.utime(path,(pkg.EPOCH,pkg.EPOCH),follow_symlinks=False)
    static=frozen.inventory(WORK/'stage');frozen.elf_dependencies(WORK/'stage')
    save(PREPARED,{'state':'prepared-reused-qualified-module','inputs':inputs,'reuse':reuse,'stage':static,
        'baseline_upgrade':baseline,'source_inode':SOURCE.stat().st_ino,'work_inode':WORK.stat().st_ino,'producer_sha256':digest(Path(__file__))})
    return {'state':'prepared-no-recompile-required','version':VERSION,'step':STEP,'stage':str(WORK/'stage')}

def qualify():
    row=read(PREPARED);_,_,reuse=original_compile()
    if GENERATION==5 and row.get('baseline_upgrade')!=upgrade4_baseline():raise ValueError('Installer5 preserved baseline changed')
    if row.get('state')!='prepared-reused-qualified-module' or row.get('reuse')!=reuse or row.get('inputs')!=source_plan() or row.get('source_inode')!=SOURCE.stat().st_ino or row.get('work_inode')!=WORK.stat().st_ino:raise ValueError('Installer4 prepared source/reuse changed')
    for name,sha in row['inputs'].items():
        if digest(SOURCE/'repository'/name)!=sha or digest(ROOT/name)!=sha:raise ValueError('Installer4 frozen current source changed')
    actual=frozen.inventory(WORK/'stage')
    if actual!=row['stage']:raise ValueError('Installer4 staged bytes changed')
    frozen.elf_dependencies(WORK/'stage');return row

def transaction(phase):
    row=read(BUILD/(STEP+'.running.json'))
    if row.get('step')!=STEP or row.get('user')!='root' or row.get('recipe_sha256')!=digest(ROOT/INSTALL) or row.get('postcheck_sha256')!=digest(ROOT/CHECK):raise ValueError('Installer4 controlled native transaction required')
    if phase=='install' and row.get('recipe_pid') not in (os.getpid(),os.getppid()):raise ValueError('Installer4 native recipe PID')
    if phase=='postcheck' and (type(row.get('recipe_exit')) is not int or row['recipe_exit']!=0):raise ValueError('Installer4 native recipe not complete')

def install():
    transaction('install');row=qualify();pkg=package()
    from dependency_preflight import native as dependencies
    dependencies(pkg.DEPENDENCIES)
    if any(os.path.lexists(path) for path in (STAGE,RECEIPT,RECEIPT.with_suffix('.part'))):raise ValueError('Installer4 preserve promotion/install outcome')
    size=sum(value.get('bytes',0) for value in row['stage']['entries'].values());payload.require_capacity(TARGET,3*size+64*1024**2)
    shutil.copytree(WORK/'stage',STAGE,symlinks=True)
    if frozen.inventory(STAGE)!=row['stage']:raise ValueError('Installer4 promotion changed')
    save(RECEIPT,{'state':'native-install-intended','prepared_sha256':digest(PREPARED),'reuse':row['reuse']})
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'toddy-installer',VERSION,str(STAGE),'--source','calamares-3.4.3.tar.gz',
        '--recipe',INSTALL,'--depends',pkg.DEPENDENCIES,'--compression-threads','2','--install'],cwd=ROOT,check=True,close_fds=True,umask=0o022)
    save(RECEIPT,{'state':'native-installed-postcheck-pending','prepared_sha256':digest(PREPARED),'reuse':row['reuse']})

def postcheck():
    transaction('postcheck');row=qualify();pkg=package()
    if frozen.native('/usr/bin/dpkg-query','-W','-f=${Version}\t${Status}','toddy-installer')!=VERSION+'\tinstall ok installed':raise ValueError('Installer4 package not configured')
    recordpath=Path('/var/log/toddy/packages')/('toddy-installer_'+VERSION+'_amd64.json');record=read(recordpath)
    archive=Path('/var/cache/toddy/packages')/('toddy-installer_'+VERSION+'_amd64.deb');control,actual,_=payload.archive_contents(archive)
    if digest(archive)!=record.get('archive_sha256') or actual!=record.get('payload') or control.get('Version')!=VERSION:raise ValueError('Installer4 native archive custody')
    for name,expected in record['payload'].items():
        path=TARGET/name.lstrip('/');info=path.lstat()
        if info.st_mode!=expected['mode'] or info.st_uid!=expected['uid'] or info.st_gid!=expected['gid']:raise ValueError('Installer4 installed metadata differs')
        if 'sha256' in expected and digest(path)!=expected['sha256']:raise ValueError('Installer4 installed bytes differ')
        if 'symlink' in expected and os.readlink(path)!=expected['symlink']:raise ValueError('Installer4 installed link differs')
    if os.path.lexists(POSTCHECK_HOME):raise ValueError('Installer4 retain existing postcheck')
    POSTCHECK_HOME.mkdir(mode=0o700)
    probe=json.loads(frozen.native('/usr/bin/env','QT_QPA_PLATFORM=offscreen','HOME=/'+POSTCHECK_HOME.relative_to(TARGET).as_posix(),
        '/'+(frozen.WORK.relative_to(TARGET)/'compile/toddy-installer-plugin-probe').as_posix(),pkg.MODULE))
    if probe.get('factory_created') is not True or probe.get('disk_writes') is not False:raise ValueError('Installer4 real no-write plugin probe failed')
    if frozen.native('/usr/bin/dpkg','--audit'):raise ValueError('Installer4 native database audit not empty')
    frozen.native('/usr/bin/apt-get','check')
    save(RECEIPT,{'state':'native-revision'+str(GENERATION)+'-package-and-reused-plugin-verified','prepared_sha256':digest(PREPARED),'reuse':row['reuse'],
        'record_sha256':digest(recordpath),'archive_sha256':digest(archive),'module_sha256':digest(TARGET/pkg.MODULE.lstrip('/')),
        'offline_payload_sha256':digest(TARGET/'usr/lib/toddy/installer/offline_payload.py'),'native_offscreen_probe':probe,
        'root_wayland_gui':'pending distinct actual GUI proof','disk_writes':False,'version':VERSION})

def main():
    if os.geteuid()!=0 or sys.argv[1:] not in (['prepare'],['qualify'],['install'],['postcheck'],['prepare5'],['qualify5'],['install5'],['postcheck5']):raise ValueError('Installer4 fixed root coordinator action')
    if sys.argv[1].endswith('5'):configure(5);sys.argv[1]=sys.argv[1][:-1]
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    if sys.argv[1] in ('prepare','qualify'):
        fd=os.open(BUILD/'build.lock',os.O_RDWR|os.O_NOFOLLOW)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if list(BUILD.glob('*.running.json')) or (BUILD/'input-sync.running').exists():raise ValueError('Installer4 active native operation')
            print(json.dumps(prepare() if sys.argv[1]=='prepare' else qualify(),sort_keys=True))
        finally:os.close(fd)
    elif sys.argv[1]=='install':install()
    else:postcheck()

if __name__=='__main__':main()
