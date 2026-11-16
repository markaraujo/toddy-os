#!/usr/bin/env python3
"""First standalone pw-cat package from frozen successful compile2, no rebuild."""
import hashlib,io,json,os,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import pipewire_tools_native as frozen
import pipewire_base_restore as restore
from verify_stage import inspect_stage
ROOT=restore.ROOT;TARGET=restore.TARGET;BUILD=restore.BUILD;LOG=restore.LOG
PACKAGE='pipewire-audio-tools';VERSION='1.6.8-1+toddy1';STEP='b09-pipewire-audio-tools-2'
INSTALL='scripts/build/phase2/pipewire_audio_tools_install.sh';CHECK='scripts/build/phase2/pipewire_audio_tools_check.sh'
STAGE=TARGET/'sources/stage/phase2-pipewire-audio-tools-2';RECEIPT=LOG/'pipewire-audio-tools-install-2.json'
DEPENDS='pipewire (= 1.6.8-1+toddy1), libsndfile (= 1.2.2-1+toddy1), glibc (= 2.44-1+toddy1), gcc-runtime (= 16.2.0-1+toddy1)'
HEADER_SOURCES=('pw-cat.c','midifile.c','midiclip.c','midievent.c','dfffile.c','dsffile.c','midifile.h','midiclip.h','midievent.h','dfffile.h','dsffile.h')


def run_packager(command,*,cwd=ROOT):
    # Keep this producer's private evidence umask; Dpkg's public DEBIAN control
    # directory is created by the child and must be at least0755.
    return subprocess.run(command,cwd=cwd,check=True,close_fds=True,umask=0o022)


def source_inputs():
    return {name:frozen.digest(frozen.regular(ROOT/name)) for name in (INSTALL,CHECK,'scripts/build/phase2/pipewire_audio_tools.py','scripts/build/phase2/pipewire_base_restore.py')}


def transaction(phase):
    row=json.loads((BUILD/(STEP+'.running.json')).read_bytes())
    if row.get('step')!=STEP or row.get('user')!='root' or row.get('recipe_sha256')!=frozen.digest(ROOT/INSTALL) or row.get('postcheck_sha256')!=frozen.digest(ROOT/CHECK):raise ValueError('pipewire_audio_tools_owned_dispatcher_required')
    if phase=='install' and row.get('recipe_pid') not in (os.getpid(),os.getppid()):raise ValueError('pipewire_audio_tools_dispatcher_pid')
    if phase=='postcheck' and (type(row.get('recipe_exit')) is not int or row['recipe_exit']!=0):raise ValueError('pipewire_audio_tools_native_recipe_not_complete')


def restoration():
    success=BUILD/(restore.STEP+'.success.json');row=json.loads(frozen.regular(success).read_bytes())
    own=frozen.regular(restore.RECEIPT);receipt=json.loads(own.read_bytes());_,failed=restore.rejected()
    if (row.get('step')!=restore.STEP or type(row.get('recipe_exit')) is not int or row['recipe_exit']!=0 or type(row.get('postcheck_exit')) is not int or row['postcheck_exit']!=0 or
            row.get('recipe_sha256')!=frozen.digest(ROOT/restore.INSTALL) or row.get('postcheck_sha256')!=frozen.digest(ROOT/restore.CHECK) or
            receipt.get('state')!='native-pipewire-base-restored' or receipt.get('old_payload_unchanged') is not True or type(receipt.get('apt_check_exit')) is not int or receipt['apt_check_exit']!=0 or
            receipt.get('old_archive_sha256')!=frozen.OLD_ARCHIVE_SHA or receipt.get('old_record_sha256')!=frozen.OLD_RECORD_SHA or receipt.get('failed_upgrade')!=failed or receipt.get('source_inputs')!=restore.source_inputs()):
        raise ValueError('pipewire_audio_tools_actual_restoration_required')
    return {'step':restore.STEP,'success_sha256':frozen.digest(success),'manifest_sha256':frozen.digest(frozen.regular(BUILD/(restore.STEP+'.manifest.json'))),
        'receipt_sha256':frozen.digest(own),'failed_upgrade':failed,'old_archive_sha256':frozen.OLD_ARCHIVE_SHA,'old_record_sha256':frozen.OLD_RECORD_SHA}


def legal_from_archive(stage,old,archive):
    """Read exact retained notices, never copy mutable installed-root files."""
    raw=subprocess.check_output(['/usr/bin/dpkg-deb','--fsys-tarfile',str(archive)],timeout=30)
    prefix='/usr/share/doc/pipewire/';destination='/usr/share/doc/'+PACKAGE+'/';copied={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as source:
        for member in source:
            virtual='/'+Path(member.name).as_posix().lstrip('./')
            if not virtual.startswith(prefix) or member.isdir():continue
            expected=old['payload'].get(virtual)
            if not member.isfile() or not expected or 'sha256' not in expected or member.uid or member.gid or member.mode!=stat.S_IMODE(expected['mode']):raise ValueError('pipewire_audio_tools_legal_member')
            data=source.extractfile(member).read()
            if hashlib.sha256(data).hexdigest()!=expected['sha256']:raise ValueError('pipewire_audio_tools_legal_custody')
            name=destination+virtual.removeprefix(prefix);path=stage/name.lstrip('/');path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(data)
            path.chmod(member.mode);copied[name]={'source_path':virtual,'sha256':expected['sha256']}
    needed={destination+'copyright',destination+'source-notices/index.json'}
    if not needed<=copied.keys() or frozen.digest(archive)!=frozen.OLD_ARCHIVE_SHA:raise ValueError('pipewire_audio_tools_complete_exact_notices_required')
    return copied


def header_data():
    # Read the complete frozen PRIVATE archive, not the legacy source ancestry.
    upstream,_=frozen.verified_source();result={}
    with tarfile.open(upstream) as source:
        for name in HEADER_SOURCES:
            member=source.getmember('pipewire-1.6.8/src/tools/'+name)
            if not member.isfile() or not 0<member.size<1024**2:raise ValueError('pipewire_audio_tools_selected_source_member')
            data=source.extractfile(member).read()
            if b'SPDX-License-Identifier: MIT' not in data[:1024]:raise ValueError('pipewire_audio_tools_selected_source_license')
            result[name]=data
    return result


def retained_headers(stage,data):
    copied={};directory=stage/'usr/share/doc'/PACKAGE/'selected-tool-source';directory.mkdir(parents=True)
    for name,value in data.items():
        target=directory/name
        with target.open('xb') as stream:stream.write(value)
        target.chmod(0o644);copied[name]={'sha256':hashlib.sha256(value).hexdigest(),'bytes':len(value),'source':'src/tools/'+name}
    return copied


def public_directories(stage):
    # Main's private evidence umask must never become installed /usr permissions.
    for path in (stage,*stage.rglob('*')):
        if path.is_dir() and not path.is_symlink():path.chmod(0o755)


def validate_stage(stage):
    observed=inspect_stage(stage);leaves={name:row for name,row in observed['entries'].items() if not row.get('directory') and not name.startswith('DEBIAN/')}
    for name,row in observed['entries'].items():
        if row.get('directory') and name!='DEBIAN' and not name.startswith('DEBIAN/') and row['mode']!=0o755:raise ValueError('pipewire_audio_tools_public_directory_mode')
        if row.get('directory') and name not in ('usr','usr/bin','usr/share','usr/share/doc','usr/share/doc/'+PACKAGE,'DEBIAN') and not name.startswith(('usr/share/doc/'+PACKAGE+'/','DEBIAN/')):raise ValueError('pipewire_audio_tools_unselected_stage_directory')
    for name,row in leaves.items():
        if name=='usr/bin/pw-cat':
            if 'sha256' not in row or row['mode']!=0o755:raise ValueError('pipewire_audio_tools_binary_mode')
        elif name in {'usr/bin/'+alias for alias in frozen.ALIASES}:
            if row.get('symlink')!='pw-cat':raise ValueError('pipewire_audio_tools_alias')
        elif name.startswith('usr/share/doc/'+PACKAGE+'/'):
            if 'sha256' not in row or row['mode']!=0o644:raise ValueError('pipewire_audio_tools_legal_mode')
        else:raise ValueError('pipewire_audio_tools_unselected_stage_path')
    if not {'usr/bin/pw-cat',*('usr/bin/'+name for name in frozen.ALIASES)}<=leaves.keys():raise ValueError('pipewire_audio_tools_incomplete_tool_set')
    if not {'usr/share/doc/'+PACKAGE+'/copyright','usr/share/doc/'+PACKAGE+'/source-manifest.json'}<=leaves.keys():raise ValueError('pipewire_audio_tools_provenance_missing')
    return {'entries':{name:row for name,row in observed['entries'].items() if name!='DEBIAN' and not name.startswith('DEBIAN/')},'payload_sha256':hashlib.sha256(json.dumps(leaves,sort_keys=True).encode()).hexdigest()}


def install():
    from dependency_preflight import native as check_dependencies
    transaction('install');proof=restoration();restore.restored_checks();prepared,tools,closure=frozen.qualify();old,archive=frozen.baseline();check_dependencies(DEPENDS)
    if any(os.path.lexists(path) for path in (STAGE,RECEIPT,RECEIPT.with_suffix('.part'),frozen.CACHE/(PACKAGE+'_'+VERSION+'_amd64.deb'),frozen.RECORDS/(PACKAGE+'_'+VERSION+'_amd64.json'))):raise ValueError('pipewire_audio_tools_existing_namespace_no_replay')
    query=subprocess.run(['/usr/sbin/chroot',str(TARGET),'/usr/bin/dpkg-query','-W','-f=${Status}',PACKAGE],capture_output=True,text=True,timeout=30)
    if query.returncode!=1:raise ValueError('pipewire_audio_tools_first_native_package_required')
    headers_data=header_data();legal_bound=frozen.archive_summary(archive)['regular_bytes']
    source_bytes=sum(row.get('bytes',0) for row in tools['entries'].values())+sum(map(len,headers_data.values()))+legal_bound
    if shutil.disk_usage(TARGET).free<16*1024**3+512*1024**2+3*source_bytes:raise ValueError('pipewire_audio_tools_preserve_16gib_reserve')
    STAGE.mkdir(mode=0o755);(STAGE/'usr/bin').mkdir(parents=True)
    for relative,row in tools['entries'].items():
        if row.get('directory'):continue
        source=frozen.WORK/'stage'/relative;target=STAGE/relative
        if 'symlink' in row:os.symlink(row['symlink'],target)
        else:shutil.copyfile(source,target);target.chmod(row['mode'])
    legal=legal_from_archive(STAGE,old,archive);headers=retained_headers(STAGE,headers_data)
    manifest={'package':PACKAGE,'version':VERSION,'upstream':'1.6.8','depends':DEPENDS,'source_inputs':source_inputs(),'restoration':proof,
        'baseline_archive_sha256':frozen.OLD_ARCHIVE_SHA,'baseline_record_sha256':frozen.OLD_RECORD_SHA,
        'frozen_source_sha256':frozen.SOURCE_SHA,'prepared_sha256':frozen.digest(frozen.PREPARED),
        'build_job_sha256':frozen.digest(LOG/(frozen.JOB+'.job.json')),'build_exit_sha256':frozen.digest(LOG/(frozen.JOB+'.exit')),
        'compiled_stage':tools,'direct_elf_closure':closure,'legal_archive_copies':legal,'selected_source_headers':headers,
        'scope':'Standalone native pw-cat only; old base/dependency pins unchanged, no model/key/service activation or audio success claim'}
    doc=STAGE/'usr/share/doc'/PACKAGE/'source-manifest.json';frozen.save(doc,manifest);doc.chmod(0o644);public_directories(STAGE);observed=validate_stage(STAGE)
    frozen.save(RECEIPT,{'version':1,'state':'native-audio-tools-install-intended-no-replay','manifest':manifest,'stage':observed})
    run_packager([sys.executable,str(ROOT/'scripts/build/stage_package.py'),PACKAGE,VERSION,str(STAGE),'--source',frozen.ARCHIVE,'--recipe',INSTALL,
        '--depends',DEPENDS,'--compression-threads','2','--install'])
    frozen.save(RECEIPT,{'version':1,'state':'native-audio-tools-installed-postcheck-pending','manifest':manifest,'stage':observed})


def postcheck():
    transaction('postcheck');receipt=json.loads(frozen.regular(RECEIPT).read_bytes())
    if receipt.get('state')!='native-audio-tools-installed-postcheck-pending' or receipt['manifest']['source_inputs']!=source_inputs() or receipt['manifest']['restoration']!=restoration():raise ValueError('pipewire_audio_tools_install_outcome_requires_reconciliation')
    if frozen.native('/usr/bin/dpkg-query','-W','-f=${Status} ${Version}',PACKAGE)!='install ok installed '+VERSION or frozen.native('/usr/bin/dpkg-query','-W','-f=${Status} ${Version}','pipewire')!='install ok installed '+frozen.OLD:raise ValueError('pipewire_audio_tools_native_versions')
    old,_=frozen.baseline();frozen.verify_old(TARGET,old['payload']);restore.reverse_pins();_,tools,closure=frozen.qualify()
    if tools!=receipt['manifest']['compiled_stage'] or closure!=receipt['manifest']['direct_elf_closure']:raise ValueError('pipewire_audio_tools_build_or_provider_changed')
    record_path=frozen.regular(frozen.RECORDS/(PACKAGE+'_'+VERSION+'_amd64.json'));record=json.loads(record_path.read_bytes());archive=frozen.regular(frozen.CACHE/(PACKAGE+'_'+VERSION+'_amd64.deb'))
    if not record.get('installed') or record.get('name')!=PACKAGE or record.get('archive_sha256')!=frozen.digest(archive):raise ValueError('pipewire_audio_tools_archive_custody')
    expected={'/'+name for name in receipt['stage']['entries']}
    if set(record['payload'])!=expected:raise ValueError('pipewire_audio_tools_native_record_namespace')
    frozen.verify_old(TARGET,record['payload'])
    for name in ('pw-cat',*frozen.ALIASES):
        if not frozen.native('/usr/bin/timeout','--kill-after=2','15','/usr/bin/'+name,'--help'):raise ValueError('pipewire_audio_tools_native_help')
    version=frozen.native('/usr/bin/pw-cat','--version')
    if 'Compiled with libpipewire 1.6.8' not in version or 'Linked with libpipewire 1.6.8' not in version:raise ValueError('pipewire_audio_tools_actual_linked_version')
    if frozen.native('/usr/bin/dpkg','--audit'):raise ValueError('pipewire_audio_tools_dpkg_audit')
    frozen.native('/usr/bin/apt-get','check')
    receipt.update(state='native-audio-tools-package-verified',old_library_payload_unchanged=True,apt_check_exit=0,
        restoration_receipt_sha256=receipt['manifest']['restoration']['receipt_sha256'],new_record_sha256=frozen.digest(record_path),new_archive_sha256=frozen.digest(archive),
        native_pwcat_sha256=record['payload']['/usr/bin/pw-cat']['sha256'],actual_audio_process_qualification='pending')
    frozen.save(RECEIPT,receipt)


def main():
    if os.getuid()!=0 or os.geteuid()!=0 or sys.argv[1:] not in (['install'],['postcheck']):raise ValueError('pipewire_audio_tools_fixed_guest_root_action')
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source "$1"; guard_target','guard',str(ROOT/'scripts/build/target.sh')],check=True)
    if sys.argv[1]=='install':install()
    else:postcheck()

if __name__=='__main__':main()
