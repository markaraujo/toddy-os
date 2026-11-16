"""First native Calamares package from the exact accepted B01 stage, no rebuild."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile

sys.dont_write_bytecode=True
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
SOURCE=TARGET/'sources/phase2/inputs/calamares-3.4.3'
ACCEPTED=TARGET/'sources/phase2/work/calamares-probe-1/stage'
STAGE=TARGET/'sources/stage/phase2-calamares-native-1'
PROBE=TARGET/'tmp/toddy-calamares-package-probe-1'
VERSION='3.4.3-1+toddy1';ARCHIVE='calamares-3.4.3.tar.gz'
SOURCE_SHA='144cbbf6bdcebfb21685950db4f0777218519df095f62f4aa392f28348110d18'
STAGE_SHA='439015aa8fd7c97674e0577862bfd8f21999a1fcb09a67976e848347334b2c03'
STEP='b12-calamares-native-1';RECEIPT=LOG/'calamares-native-install-1.json'
RECORDS=Path('/var/log/toddy/packages');CACHE=Path('/var/cache/toddy/packages')
PROVIDERS={'gcc-runtime':'16.2.0-1+toddy1','glibc':'2.44-1+toddy1',
    'kcoreaddons':'6.29.0-1+toddy1','python':'3.14.10-1+toddy2',
    'qtbase':'6.11.2-1+toddy2','qtsvg':'6.11.2-1+toddy1','yaml-cpp':'0.9.0-1+toddy1'}
DEPENDS=', '.join(name+' (= '+version+')' for name,version in sorted(PROVIDERS.items()))


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def native(*args):
    return subprocess.check_output(['/usr/sbin/chroot',str(TARGET),'/usr/bin/env','-i',
        'PATH=/usr/bin:/usr/sbin','HOME=/root','LC_ALL=C',*args],text=True,timeout=90).strip()


def save(path,value):
    part=path.with_suffix('.part')
    with part.open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    part.replace(path)


def source_configuration():
    cache=ACCEPTED.parent/'compile/CMakeCache.txt'
    values={}
    for line in cache.read_text().splitlines():
        match=re.fullmatch(r'([^:#]+):[^=]+=(.*)',line)
        if match:values[match[1]]=match[2]
    required={'INSTALL_CONFIG':'OFF','INSTALL_POLKIT':'OFF','WITH_PYBIND11':'ON',
        'WITH_PYTHON':'ON','WITH_QML':'OFF','CMAKE_HOME_DIRECTORY':'/src'}
    if any(values.get(key)!=value for key,value in required.items()):
        raise ValueError('Calamares B01 source build configuration differs')
    modules={path.name for path in (SOURCE/'src/modules').iterdir() if path.is_dir()}
    skipped=values.get('SKIP_MODULES','').split(';')
    if not modules or len(skipped)!=len(set(skipped)) or set(skipped)!=modules:
        raise ValueError('Calamares B01 upstream modules are not all skipped')
    # No undeclared compatibility patch is assumed. Compare frozen archive source
    # files read-only; additional B01 fixtures are not included in this package.
    count=0;total=0
    with tarfile.open(TARGET/'sources'/ARCHIVE,'r:gz') as archive:
        for member in archive:
            parts=Path(member.name).parts
            if not parts or parts[0]!='calamares-3.4.3' or '..' in parts:
                raise ValueError('Calamares frozen source archive namespace')
            relative=Path(*parts[1:])
            if not parts[1:]:continue
            target=SOURCE/relative
            if member.isfile():
                count+=1;total+=member.size
                if count>100000 or member.size>32*1024**2 or total>256*1024**2 or target.resolve()!=target or not target.is_file():
                    raise ValueError('Calamares frozen source file custody')
                if hashlib.file_digest(archive.extractfile(member),'sha256').hexdigest()!=digest(target):
                    raise ValueError('Calamares undeclared source patch: '+str(relative))
            elif member.issym():
                if not target.is_symlink() or str(target.readlink())!=member.linkname:raise ValueError('Calamares source link differs')
            elif not member.isdir():raise ValueError('Calamares unknown frozen source member')
    if not count:raise ValueError('Calamares empty source archive')
    return {'cache_sha256':digest(cache),'frozen_source_files':count,'frozen_source_bytes':total,
        'skipped_modules':sorted(modules),'unrecorded_source_patch':False}


def accepted_stage():
    from verify_stage import inspect_stage
    proof=json.loads((ROOT/'docs/evidence/B01-calamares-native-probe.json').read_bytes())
    if proof['command_exit']!=0 or proof['consumer_job']!='calamares-probe-4' or proof['stage_manifest_sha256']!=STAGE_SHA:
        raise ValueError('Calamares accepted B01 stage proof differs')
    if (LOG/'calamares-probe-4.exit').read_text().strip()!='0':raise ValueError('Calamares B01 native consumer not complete')
    if digest(TARGET/'sources'/ARCHIVE)!=SOURCE_SHA:raise ValueError('Calamares frozen upstream source differs')
    if ACCEPTED.resolve()!=ACCEPTED:raise ValueError('Calamares redirected accepted stage')
    observed=inspect_stage(ACCEPTED)
    if observed['manifest_sha256']!=STAGE_SHA or len(observed['entries'])!=373 or sum(row.get('bytes',0) for row in observed['entries'].values())!=5468441:
        raise ValueError('Calamares accepted stage changed; never rebuild or repair it here')
    for relative,row in observed['entries'].items():
        if not row.get('directory') and relative.startswith(('etc/','usr/share/polkit-1/','usr/lib/calamares/modules/','usr/libexec/')):
            raise ValueError('Calamares upstream config/Polkit/module execution is not qualified')
    return observed


def dependency_state():
    result={}
    for name,version in sorted(PROVIDERS.items()):
        if native('/usr/bin/dpkg-query','-W','-f=${Version}\t${Status}',name)!=version+'\tinstall ok installed':
            raise ValueError('Calamares frozen dependency absent/different: '+name)
        record=RECORDS/(name+'_'+version+'_amd64.json')
        value=json.loads(record.read_bytes());archive=CACHE/(name+'_'+version+'_amd64.deb')
        if value.get('installed') is not True or digest(archive)!=value['archive_sha256']:
            raise ValueError('Calamares dependency native archive custody')
        result[name]={'version':version,'record_sha256':digest(record),'archive_sha256':value['archive_sha256']}
    return result


def elf_dependencies(stage):
    from audit_native_elf import target_resolve
    owners={}
    for listing in (TARGET/'var/lib/dpkg/info').glob('*.list'):
        name=listing.name.removesuffix('.list').split(':')[0]
        for virtual in listing.read_text().splitlines():owners.setdefault(virtual.rstrip('/'),set()).add(name)
    external=set();checked=0
    for path in stage.rglob('*'):
        if path.is_symlink() or not path.is_file():continue
        with path.open('rb') as stream:
            if stream.read(4)!=b'\x7fELF':continue
        checked+=1
        dynamic=subprocess.check_output(['/usr/bin/readelf','-d',str(path)],text=True)
        for kind,value in re.findall(r'\((NEEDED|RPATH|RUNPATH)\).*\[(.*?)\]',dynamic):
            if kind!='NEEDED':raise ValueError('Calamares unexpected runtime search path')
            if not value or '/' in value:raise ValueError('Calamares unknown provider name')
            internal=stage/'usr/lib'/value
            if internal.is_file() and internal.resolve().is_relative_to(stage):continue
            provider,canonical=target_resolve(TARGET,'/usr/lib/'+value)
            found=owners.get(canonical,set())|owners.get('/usr/lib/'+value,set())
            if not provider.is_file() or len(found)!=1 or not found<=PROVIDERS.keys():
                raise ValueError('Calamares undeclared/ambiguous ELF owner: '+value+' '+repr(found))
            owner=next(iter(found))
            record=RECORDS/(owner+'_'+PROVIDERS[owner]+'_amd64.json')
            entry=json.loads(record.read_bytes())['payload'].get(canonical,{})
            if entry.get('sha256')!=digest(provider):raise ValueError('Calamares native ELF provider bytes differ')
            external.update(found)
    if checked<3 or external!=set(PROVIDERS):raise ValueError('Calamares direct provider inventory differs')
    return {'elf_files':checked,'providers':sorted(external),'undeclared_direct_providers':0}


def qualify():
    observed=accepted_stage();source=source_configuration();dependencies=dependency_state();closure=elf_dependencies(ACCEPTED)
    closure['source_configuration']=source
    query=subprocess.run(['/usr/sbin/chroot',str(TARGET),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','LC_ALL=C',
        '/usr/bin/dpkg-query','-W','-f=${Status}','calamares'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=30)
    if query.returncode!=1:
        raise ValueError('Calamares native absence not established; reconcile, never replay first package')
    return observed,dependencies,closure


def transaction(phase):
    value=json.loads((Path('/var/log/toddy/build')/(STEP+'.running.json')).read_bytes())
    if (value.get('step')!=STEP or value.get('user')!='root' or
            value.get('recipe_sha256')!=digest(ROOT/'scripts/build/phase2/calamares_native_install.sh') or
            value.get('postcheck_sha256')!=digest(ROOT/'scripts/build/phase2/calamares_native_check.sh')):
        raise ValueError('Calamares owned dispatcher transaction required')
    if phase=='install' and value.get('recipe_pid') not in (os.getpid(),os.getppid()):raise ValueError('Calamares dispatcher PID differs')
    if phase=='postcheck' and (type(value.get('recipe_exit')) is not int or value['recipe_exit']!=0):raise ValueError('Calamares recipe completion not established')


def staged_consumer():
    if os.path.lexists(PROBE):raise ValueError('Preserve Calamares native consumer generation')
    PROBE.mkdir(mode=0o700);(PROBE/'runtime').mkdir(mode=0o700)
    virtual='/'+PROBE.relative_to(TARGET).as_posix()
    command=['/usr/sbin/chroot',str(TARGET),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin',
        'HOME='+virtual,'LC_ALL=C','QT_QPA_PLATFORM=offscreen','XDG_RUNTIME_DIR='+virtual+'/runtime',
        'LD_LIBRARY_PATH=/sources/phase2/work/calamares-probe-1/stage/usr/lib',
        '/usr/bin/timeout','--kill-after=5','45',
        '/sources/phase2/work/calamares-probe-1/stage/usr/bin/calamares','--version']
    with (PROBE/'version.log').open('xb') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=False,close_fds=True)
        log.flush();os.fsync(log.fileno())
    result.check_returncode()
    if not re.search(r'calamares\s*3\.4\.3', (PROBE/'version.log').read_text(), re.IGNORECASE):
        raise ValueError('Calamares current-Qt offscreen version consumer differs')
    return digest(PROBE/'version.log')


def install():
    from package_copyright import write_copyright
    from verify_stage import inspect_stage
    transaction('install')
    if os.path.lexists(STAGE) or RECEIPT.exists():raise ValueError('Preserve Calamares existing package intent/stage')
    observed,dependencies,closure=qualify()
    space=os.statvfs(TARGET);size=sum(row.get('bytes',0) for row in observed['entries'].values())
    if space.f_bavail*space.f_frsize<16*1024**3+3*size+64*1024**2:raise ValueError('Calamares native package reserve')
    consumer=staged_consumer()
    shutil.copytree(ACCEPTED,STAGE,symlinks=True)
    if inspect_stage(STAGE)!=observed:raise ValueError('Calamares promotion differs')
    write_copyright(STAGE,'calamares',[ARCHIVE])
    state={'state':'native-install-intended','version':VERSION,'accepted_stage_sha256':STAGE_SHA,
        'source_sha256':SOURCE_SHA,'dependencies':dependencies,'closure':closure,
        'current_qt_offscreen_consumer_sha256':consumer,'production_gui_qualified':False}
    save(RECEIPT,state)
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'calamares',VERSION,str(STAGE),
        '--source',ARCHIVE,'--recipe','scripts/build/phase2/calamares_native_install.sh',
        '--depends',DEPENDS,'--compression-threads','2','--install'],cwd=ROOT,check=True,close_fds=True)
    state['state']='native-installed-postcheck-pending';save(RECEIPT,state)


def postcheck():
    transaction('postcheck')
    state=json.loads(RECEIPT.read_bytes())
    if state['state']!='native-installed-postcheck-pending':raise ValueError('Calamares install outcome requires reconciliation')
    if native('/usr/bin/dpkg-query','-W','-f=${Version}\t${Status}','calamares')!=VERSION+'\tinstall ok installed':raise ValueError('Calamares native package not configured')
    if dependency_state()!=state['dependencies']:raise ValueError('Calamares frozen providers changed')
    accepted_stage()
    if source_configuration()!=state['closure']['source_configuration']:raise ValueError('Calamares B01 source/cache changed')
    from verify_stage import inspect_stage
    for relative,row in inspect_stage(STAGE)['entries'].items():
        if relative.startswith('DEBIAN/') or row.get('directory'):continue
        actual=TARGET/relative
        if 'symlink' in row:
            if not actual.is_symlink() or str(actual.readlink())!=row['symlink']:raise ValueError('Calamares installed link differs')
        elif actual.is_symlink() or digest(actual)!=row['sha256']:raise ValueError('Calamares installed file differs')
        info=actual.lstat()
        if info.st_uid or info.st_gid or stat.S_IMODE(info.st_mode)!=row['mode']:raise ValueError('Calamares installed metadata differs')
    if native('/usr/bin/dpkg','--audit'):raise ValueError('Calamares native database audit')
    native('/usr/bin/apt-get','check')
    version=native('/usr/bin/env','QT_QPA_PLATFORM=offscreen','/usr/bin/calamares','--version')
    if not re.search(r'calamares\s*3\.4\.3',version,re.IGNORECASE):raise ValueError('Calamares installed current-Qt consumer differs')
    state.update(state='native-package-and-offscreen-consumer-verified',
        pending=['actual root Wayland GUI authorization/rendering','custom Toddy module','blank-disk install and BIOS/UEFI boots'])
    save(RECEIPT,state)


def main():
    if os.getuid()!=0 or os.geteuid()!=0 or sys.argv[1:] not in (['qualify'],['install'],['postcheck']):raise ValueError('Calamares fixed root coordinator action')
    subprocess.run(['/usr/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    {'qualify':qualify,'install':install,'postcheck':postcheck}[sys.argv[1]]()


if __name__=='__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
