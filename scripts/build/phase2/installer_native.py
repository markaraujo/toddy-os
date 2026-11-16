#!/usr/bin/env python3
"""Coordinator-only native module preparation/promotion; never a host installer."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs')
SOURCE=TARGET/'sources/phase2/inputs/toddy-installer-0.2.0'
WORK=TARGET/'sources/phase2/work/toddy-installer-1'
STAGE=TARGET/'sources/stage/phase2-toddy-installer-1'
LOG=Path('/var/log/toddy/phase2');PREPARED=LOG/'toddy-installer-prepared-1.json'
VERSION='0.2.0-1+toddy1';STEP='b12-toddy-installer-1';JOB='toddy-installer-build-1'


def package_module():
    try:from . import installer_package
    except ImportError:import installer_package
    return installer_package

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def available(path):
    value=os.statvfs(path);return value.f_bavail*value.f_frsize


def save(path,value):
    part=path.with_suffix('.part')
    with part.open('x') as stream:json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    part.replace(path)


def native(*arguments):
    return subprocess.check_output(['/usr/bin/chroot',str(TARGET),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','HOME=/root','LC_ALL=C',*arguments],text=True).strip()


def package_state():
    result={}
    expected={'calamares':'3.4.3-1+toddy1','qtbase':'6.11.2-1+toddy2'}
    for name,version in expected.items():
        actual=native('/usr/bin/dpkg-query','-W','-f=${Version}\t${Status}',name)
        if actual!=version+'\tinstall ok installed':raise ValueError('installer_frozen_native_dependency_missing')
        record=Path('/var/log/toddy/packages')/(name+'_'+version+'_amd64.json');value=json.loads(record.read_bytes())
        archive=Path('/var/cache/toddy/packages')/(name+'_'+version+'_amd64.deb')
        if value.get('installed') is not True or digest(archive)!=value['archive_sha256']:raise ValueError('installer_native_dependency_custody')
        result[name]={'version':version,'record_sha256':digest(record),'archive_sha256':value['archive_sha256']}
    return result


def prepare():
    package=package_module()
    if SOURCE.exists() or SOURCE.is_symlink() or WORK.exists() or WORK.is_symlink() or PREPARED.exists():raise ValueError('installer_prepare_preserve_existing')
    if available(TARGET)<17*1024**3:raise ValueError('installer_preserve_16gib_floor')
    before=package_state();inputs,_,_=package.plan(ROOT)
    for name in package.COMPILE_INPUTS:inputs['runtime/installer/calamares/'+name]=digest(ROOT/'runtime/installer/calamares'/name)
    inputs['scripts/build/phase2/installer_build.py']=digest(ROOT/'scripts/build/phase2/installer_build.py')
    inputs['scripts/build/phase2/installer_build.sh']=digest(ROOT/'scripts/build/phase2/installer_build.sh')
    state={'state':'preparing','source':str(SOURCE),'work':str(WORK),'before':before,'inputs':inputs,
           'harness_sha256':digest(ROOT/'scripts/build/phase2/isolated.sh')}
    save(PREPARED,state)
    SOURCE.mkdir(mode=0o755);(SOURCE/'repository').mkdir(mode=0o755)
    for relative,sha in sorted(inputs.items()):
        source=ROOT/relative
        if source.resolve()!=source or source.is_symlink() or digest(source)!=sha:raise ValueError('installer_prepare_source_changed')
        destination=SOURCE/'repository'/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination);destination.chmod(0o444)
    for name in ('installer_build.py','installer_build.sh'):
        shutil.copyfile(ROOT/'scripts/build/phase2'/name,SOURCE/name);(SOURCE/name).chmod(0o444)
    WORK.mkdir(mode=0o755);os.chown(WORK,101,101)
    for path in SOURCE.rglob('*'):
        if path.is_dir():path.chmod(0o555)
    SOURCE.chmod(0o555)
    state.update(state='prepared',source_inode=SOURCE.stat().st_ino,work_inode=WORK.stat().st_ino)
    save(PREPARED,state)



def read_stage_manifest(stage):
    package=package_module();stage=Path(stage)
    if stage.resolve()!=stage or stage.is_symlink():raise ValueError('installer_redirected_stage')
    path=stage
    for part in ('usr','share','doc','toddy-installer','source-manifest.json'):
        path/=part
        if path.is_symlink():raise ValueError('installer_redirected_stage_manifest')
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>2*1024*1024:raise ValueError('installer_stage_manifest_custody')
    return package.artifact_json(path.read_bytes())

def inventory(stage):
    package=package_module()
    root=Path(stage);manifest=read_stage_manifest(root)
    expected=set(manifest['files'])|set(manifest['dependency_links'])|{'/usr/share/doc/toddy-installer/source-manifest.json'}
    actual={};files=set()
    for base,directories,leaves in os.walk(root,followlinks=False):
        for name in directories+leaves:
            path=Path(base)/name;relative='/'+path.relative_to(root).as_posix();info=path.lstat()
            if os.listxattr(path,follow_symlinks=False) or info.st_mode&0o6000 or not stat.S_ISLNK(info.st_mode) and info.st_mode&0o002:raise ValueError('installer_privileged_or_extended_stage')
            row={'mode':stat.S_IMODE(info.st_mode)}
            if path.is_symlink():
                if manifest['dependency_links'].get(relative)!=os.readlink(path):raise ValueError('installer_unknown_dependency_link')
                row['symlink']=os.readlink(path);files.add(relative)
            elif path.is_dir():row['directory']=True
            elif path.is_file():
                row['sha256']=digest(path);row['bytes']=info.st_size;files.add(relative)
                if relative in manifest['files'] and (row['sha256']!=manifest['files'][relative]['sha256'] or format(row['mode'],'04o')!=manifest['files'][relative]['mode']):raise ValueError('installer_staged_bytes_changed')
            else:raise ValueError('installer_special_stage_file')
            actual[relative]=row
    if files!=expected or manifest['live_only'] is not True or manifest['offline_base'] is not False or manifest['native_root_gui_qualified'] is not False:
        raise ValueError('installer_stage_namespace_or_scope')
    return {'manifest_sha256':hashlib.sha256(package.encoded(actual)).hexdigest(),'entries':actual}



def verify_source_plan(stage,binary,receipt):
    package=package_module();inputs,files,links=package.plan(ROOT)
    files[package.MODULE]=(binary,0o644)
    files['/usr/share/doc/toddy-installer/native-module-compile.json']=(package.encoded(receipt),0o644)
    expected={name:{'sha256':package.sha(data),'bytes':len(data),'mode':format(mode,'04o')} for name,(data,mode) in files.items()}
    manifest=read_stage_manifest(stage)
    keys={'schema_version','package','version','architecture','live_only','offline_base','dependencies','inputs','files','dependency_links',
          'module_sha256','native_compile_receipt_sha256','native_root_gui_qualified','desktop_hidden_until_native_promotion',
          'bundled_composition_qualification','bundled_credentials','bundled_grants','branding_owner','upstream_calamares_owned_paths_modified'}
    if set(manifest)!=keys:raise ValueError('installer_stage_manifest_schema')
    constants={'schema_version':1,'package':package.PACKAGE,'version':package.VERSION,'architecture':'amd64','live_only':True,'offline_base':False,
               'dependencies':package.DEPENDENCIES,'native_root_gui_qualified':False,'desktop_hidden_until_native_promotion':True,
               'bundled_composition_qualification':False,'bundled_credentials':False,'bundled_grants':False,
               'branding_owner':'calamares-branding-toddy','upstream_calamares_owned_paths_modified':False}
    if package.encoded({key:manifest.get(key) for key in constants})!=package.encoded(constants):raise ValueError('installer_stage_qualification_or_scope_changed')
    if manifest.get('inputs')!=inputs or manifest.get('files')!=expected or manifest.get('dependency_links')!=links or \
            manifest.get('package')!=package.PACKAGE or manifest.get('version')!=package.VERSION or manifest.get('dependencies')!=package.DEPENDENCIES or \
            manifest.get('module_sha256')!=package.sha(binary) or manifest.get('native_compile_receipt_sha256')!=package.sha(package.encoded(receipt)):
        raise ValueError('installer_stage_differs_from_independent_source_plan')

def qualify():
    package=package_module()
    prepared=json.loads(PREPARED.read_bytes())
    if prepared['state']!='prepared' or prepared['before']!=package_state() or prepared['harness_sha256']!=digest(ROOT/'scripts/build/phase2/isolated.sh'):
        raise ValueError('installer_prepared_native_context_changed')
    if SOURCE.stat().st_ino!=prepared['source_inode'] or WORK.stat().st_ino!=prepared['work_inode']:raise ValueError('installer_prepared_inodes_changed')
    for relative,sha in prepared['inputs'].items():
        if digest(SOURCE/'repository'/relative)!=sha or digest(ROOT/relative)!=sha:raise ValueError('installer_prepared_source_changed')
    if (LOG/(JOB+'.exit')).read_text().strip()!='0':raise ValueError('installer_isolated_compile_not_passed')
    job=json.loads((LOG/(JOB+'.job.json')).read_bytes())
    expected=['/bin/bash',str(ROOT/'scripts/build/phase2/isolated.sh'),str(SOURCE),str(WORK),'bash','/src/installer_build.sh']
    if job.get('command')!=expected or job.get('harness_sha256')!=prepared['harness_sha256']:
        raise ValueError('installer_isolated_compile_receipt_missing')
    module=WORK/'compile/libcalamares_viewmodule_toddy.so'
    binary,receipt=package.validate_module(module,WORK/'native-module-compile.json',ROOT)
    verify_source_plan(WORK/'stage',binary,receipt)
    result=inventory(WORK/'stage');elf_dependencies(WORK/'stage')
    return prepared,result



def elf_dependencies(stage):
    """Readback of every direct module provider before promotion/package writes."""
    try:from ..audit_native_elf import target_resolve
    except ImportError:
        sys.path.insert(0,str(ROOT/'scripts/build'))
        from audit_native_elf import target_resolve
    package=package_module();declared=set(re.findall(r'(?:^|,)\s*([a-z0-9][a-z0-9+.-]*)',package.DEPENDENCIES))
    owners={}
    for listing in (TARGET/'var/lib/dpkg/info').glob('*.list'):
        name=listing.name.removesuffix('.list').split(':')[0]
        for virtual in listing.read_text().splitlines():owners.setdefault(virtual.rstrip('/'),set()).add(name)
    checked=0
    for path in Path(stage).rglob('*'):
        if path.is_symlink() or not path.is_file():continue
        with path.open('rb') as stream:
            if stream.read(4)!=b'\x7fELF':continue
        checked+=1
        dynamic=subprocess.check_output(['/usr/bin/readelf','-d',str(path)],text=True)
        for kind,value in re.findall(r'\((NEEDED|RPATH|RUNPATH)\).*\[(.*?)\]',dynamic):
            if kind!='NEEDED':raise ValueError('installer_module_runtime_search_path')
            if '/' in value or not value:raise ValueError('installer_unknown_elf_provider_name')
            provider,canonical=target_resolve(TARGET,'/usr/lib/'+value)
            found=owners.get(canonical,set())|owners.get('/usr/lib/'+value,set())
            if not provider.is_file() or len(found)!=1 or not found<=declared:raise ValueError('installer_undeclared_native_elf_provider')
    if checked!=1:raise ValueError('installer_unexpected_native_binary_closure')
    return {'elf_files':checked,'undeclared_direct_providers':0,'depends':package.DEPENDENCIES}

def transaction(phase):
    marker=Path('/var/log/toddy/build')/(STEP+'.running.json')
    value=json.loads(marker.read_bytes())
    if value.get('step')!=STEP or value.get('user')!='root' or value.get('recipe_sha256')!=digest(ROOT/'scripts/build/phase2/installer_install.sh') or value.get('postcheck_sha256')!=digest(ROOT/'scripts/build/phase2/installer_check.sh'):
        raise ValueError('installer_native_transaction_boundary_required')
    if phase=='install' and value['recipe_pid'] not in (os.getpid(),os.getppid()):raise ValueError('installer_wrong_native_transaction')
    if phase=='postcheck' and (type(value.get('recipe_exit')) is not int or value.get('recipe_exit')!=0):raise ValueError('installer_native_recipe_not_passed')


def install():
    package=package_module()
    from dependency_preflight import native as check_dependencies
    transaction('install');prepared,static=qualify();check_dependencies(package.DEPENDENCIES)
    if STAGE.exists() or STAGE.is_symlink():raise ValueError('installer_promotion_exists')
    size=sum(row.get('bytes',0) for row in static['entries'].values())
    if available(TARGET)<16*1024**3+3*size+64*1024**2:raise ValueError('installer_preserve_16gib_floor')
    shutil.copytree(WORK/'stage',STAGE,symlinks=True)
    if inventory(STAGE)!=static:raise ValueError('installer_promotion_changed')
    receipt=LOG/'toddy-installer-install-1.json'
    if receipt.exists():raise ValueError('installer_native_install_requires_reconciliation')
    save(receipt,{'state':'native-install-intended','stage_manifest_sha256':static['manifest_sha256'],'native_root_gui_qualified':False})
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'toddy-installer',VERSION,str(STAGE),
        '--source','calamares-3.4.3.tar.gz','--recipe','scripts/build/phase2/installer_install.sh','--depends',package.DEPENDENCIES,
        '--compression-threads','2','--install'],cwd=ROOT,check=True,close_fds=True)
    save(receipt,{'state':'native-installed-postcheck-pending','stage_manifest_sha256':static['manifest_sha256'],'native_root_gui_qualified':False})


def postcheck():
    transaction('postcheck')
    if native('/usr/bin/dpkg-query','-W','-f=${Version}\t${Status}','toddy-installer')!=VERSION+'\tinstall ok installed':raise ValueError('installer_package_not_configured')
    root=TARGET/'usr/lib/toddy/installer'
    for name in ('composition.py','native_finalizer.py','installed_boot.py','launch.py'):
        if digest(root/name)!=digest(ROOT/'runtime/installer'/name):raise ValueError('installer_installed_source_changed')
    package=package_module()
    if digest(TARGET/package.MODULE.lstrip('/'))!=digest(WORK/'compile/libcalamares_viewmodule_toddy.so'):raise ValueError('installer_installed_module_changed')
    # An actual no-write plugin/ABI probe is distinct from the still-unverified
    # root Calamares Wayland GUI. Never use Calamares --test to bypass root.
    home=TARGET/'tmp/toddy-installer-offscreen-postcheck-1'
    if home.exists() or home.is_symlink():raise ValueError('installer_postcheck_preserve_existing')
    home.mkdir(mode=0o700)
    output=native('/usr/bin/env','QT_QPA_PLATFORM=offscreen','HOME=/tmp/toddy-installer-offscreen-postcheck-1',
                  '/'+(WORK.relative_to(TARGET)/'compile/toddy-installer-plugin-probe').as_posix(),package.MODULE)
    probe=json.loads(output)
    if probe.get('factory_created') is not True or probe.get('disk_writes') is not False:raise ValueError('installer_native_plugin_postcheck')
    if (TARGET/'usr/share/toddy/installer/launch-qualification.json').exists():raise ValueError('installer_unexpected_factory_launch_qualification')
    print(json.dumps({'state':'native-package-and-offscreen-plugin-verified','root_wayland_gui':'pending','blank_disk_boot':'pending','disk_writes':False},sort_keys=True))


def main():
    if os.getuid()!=0 or os.geteuid()!=0 or len(sys.argv)!=2 or sys.argv[1] not in ('prepare','qualify','install','postcheck'):raise SystemExit('installer_native_coordinator_root_required')
    subprocess.run(['/bin/bash','-c','source "$1"; guard_target','guard',str(ROOT/'scripts/build/target.sh')],check=True)
    LOG.mkdir(parents=True,exist_ok=True)
    if sys.argv[1]=='prepare':
        fd=os.open('/var/log/toddy/build/build.lock',os.O_RDWR|os.O_CREAT,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if list(Path('/var/log/toddy/build').glob('*.running.json')):raise ValueError('installer_existing_native_recipe')
            prepare()
        finally:os.close(fd)
    elif sys.argv[1]=='qualify':print(json.dumps(qualify()[1],sort_keys=True))
    elif sys.argv[1]=='install':install()
    else:postcheck()

if __name__=='__main__':main()
