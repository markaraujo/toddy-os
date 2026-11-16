#!/usr/bin/env python3
"""Frozen PipeWire pw-cat addition; old native payload is an immutable baseline."""
import fcntl,hashlib,io,json,os,re,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from verify_stage import inspect_stage

ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs');LOG=Path('/var/log/toddy/phase2')
RECORDS=Path('/var/log/toddy/packages');CACHE=Path('/var/cache/toddy/packages')
SOURCE=TARGET/'sources/phase2/inputs/pipewire-tools-1';WORK=TARGET/'sources/phase2/work/pipewire-tools-1'
STAGE=TARGET/'sources/stage/phase2-pipewire-tools-1';PREPARED=LOG/'pipewire-tools-prepared-1.json';RECEIPT=LOG/'pipewire-tools-install-1.json'
OLD='1.6.8-1+toddy1';VERSION='1.6.8-1+toddy2';ARCHIVE='pipewire-1.6.8.tar.bz2'
SOURCE_BYTES=2062635
SOURCE_CUSTODY=LOG/'pipewire-tools-source-custody-1'
PRIVATE_ARCHIVE=SOURCE_CUSTODY/ARCHIVE
SOURCE_SHA='efbaedf80450e5b08bb3196a4ca7ea17850d4a71ec1a8ae321e8937a7c95779e'
OLD_RECORD_SHA='ebdad900696ab299bcc7be52dcbde490c0a2a6d5afb3b659acb89cb6c2a77303'
OLD_ARCHIVE_SHA='6fcccccb584101ebf0899dcabbc64ff8551f8cc4e58356bc8878febc6a17c56a'
OLD_DEPENDS='glibc (>= 2.44-1), systemd (>= 261.2-1), dbus (>= 1.16.2-1), glib (>= 2.88.3-1+toddy1), alsa-lib (= 1.2.16.1-1+toddy1)'
DEPENDS=OLD_DEPENDS+', libsndfile (= 1.2.2-1+toddy1), gcc-runtime (= 16.2.0-1+toddy1)'
PROVIDERS={'pipewire':OLD,'libsndfile':'1.2.2-1+toddy1','glibc':'2.44-1+toddy1','gcc-runtime':'16.2.0-1+toddy1'}
ALIASES=('pw-play','pw-record','pw-midiplay','pw-midirecord','pw-midi2play','pw-midi2record','pw-dsdplay','pw-encplay','pw-sysex')
STEP='b09-pipewire-tools-1';JOB='pipewire-tools-build-1';INSTALL='scripts/build/phase2/pipewire_tools_install.sh';CHECK='scripts/build/phase2/pipewire_tools_check.sh'
BUILD='scripts/build/phase2/pipewire_tools_build.sh'


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def save(path,value):
    part=path.with_suffix('.part')
    with part.open('x') as stream:os.fchmod(stream.fileno(),0o600);json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    part.replace(path)
    directory=os.open(path.parent,os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)

def regular(path):
    path=Path(path)
    if path.resolve()!=path:raise ValueError('pipewire_tools_redirected_input')
    for item in (path,*path.parents):
        info=item.lstat()
        if info.st_uid or info.st_mode&0o022:raise ValueError('pipewire_tools_unowned_input')
    info=path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise ValueError('pipewire_tools_regular_input')
    return path


def source_fingerprint(info):
    # This fixed historical LFS cache is group-writable. Integrity comes from
    # the frozen SHA plus stable opened FD, never trust in its directory owner.
    if (not stat.S_ISREG(info.st_mode) or info.st_uid or info.st_gid or info.st_nlink!=1 or
            stat.S_IMODE(info.st_mode) not in (0o644,0o664) or info.st_size!=SOURCE_BYTES):
        raise ValueError('pipewire_tools_legacy_source_metadata')
    return {key:getattr(info,'st_'+key) for key in ('dev','ino','mode','uid','gid','nlink','size','atime_ns','mtime_ns','ctime_ns')}


def verified_source():
    archive=regular(PRIVATE_ARCHIVE);receipt=regular(SOURCE_CUSTODY/'source-custody.json')
    if stat.S_IMODE(SOURCE_CUSTODY.stat().st_mode)!=0o700 or stat.S_IMODE(receipt.stat().st_mode)!=0o600:raise ValueError('pipewire_tools_private_source_mode')
    state=json.loads(receipt.read_bytes())
    if state.get('state')!='frozen-private-source-verified' or state.get('sha256')!=SOURCE_SHA or state.get('bytes')!=SOURCE_BYTES or archive.stat().st_size!=SOURCE_BYTES or digest(archive)!=SOURCE_SHA:
        raise ValueError('pipewire_tools_private_source_changed')
    if stat.S_IMODE(archive.stat().st_mode)!=0o600:raise ValueError('pipewire_tools_private_source_mode')
    return archive,state



def protected_source_parent():
    # Check protected OUTPUT ancestry only. Do not relax regular() for inputs.
    if LOG.resolve()!=LOG:raise ValueError('pipewire_tools_source_custody_parent')
    for path in (LOG,*LOG.parents):
        info=path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid or info.st_mode&0o022:raise ValueError('pipewire_tools_source_custody_parent')


def copy_frozen_source():
    """One fixed cache file through a pinned FD, into fresh protected custody."""
    if os.path.lexists(SOURCE_CUSTODY):raise ValueError('pipewire_tools_source_custody_exists_no_replay')
    protected_source_parent()
    original=TARGET/'sources'/ARCHIVE
    if original.parent.resolve()!=original.parent:raise ValueError('pipewire_tools_redirected_legacy_cache')
    fd=os.open(original,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NOATIME)
    try:
        before=source_fingerprint(os.fstat(fd))
        if source_fingerprint(original.lstat())!=before:raise ValueError('pipewire_tools_legacy_source_path_changed')
        SOURCE_CUSTODY.mkdir(mode=0o700)
        directory=os.open(LOG,os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
        intent={'version':1,'state':'copy-intended-no-replay','source':str(original),'source_metadata':before,
            'sha256':SOURCE_SHA,'bytes':SOURCE_BYTES,'producer_sha256':digest(Path(__file__))}
        save(SOURCE_CUSTODY/'source-custody.json',intent)
        actual=hashlib.sha256();count=0
        out=os.open(PRIVATE_ARCHIVE,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(out,'wb') as stream:
            while chunk:=os.read(fd,1024**2):
                count+=len(chunk)
                if count>SOURCE_BYTES:raise ValueError('pipewire_tools_legacy_source_size_changed')
                actual.update(chunk);stream.write(chunk)
            stream.flush();os.fsync(stream.fileno())
        if count!=SOURCE_BYTES or actual.hexdigest()!=SOURCE_SHA or source_fingerprint(os.fstat(fd))!=before or source_fingerprint(original.lstat())!=before:
            raise ValueError('pipewire_tools_legacy_source_bytes_or_identity_changed')
        if digest(PRIVATE_ARCHIVE)!=SOURCE_SHA:raise ValueError('pipewire_tools_private_source_copy_differs')
        intent['state']='frozen-private-source-verified';save(SOURCE_CUSTODY/'source-custody.json',intent)
        for path in (SOURCE_CUSTODY,LOG):
            directory=os.open(path,os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
        return verified_source()
    finally:os.close(fd)


def native(*args,binary=False):
    result=subprocess.check_output(['/usr/sbin/chroot',str(TARGET),'/usr/bin/env','-i','PATH=/usr/bin:/usr/sbin','HOME=/root','LC_ALL=C',*args],timeout=90)
    return result if binary else result.decode().strip()


def patch_tag(source):
    file=source/'src/tools/meson.build';before=file.read_bytes()
    needle=b"  pw_cat = executable('pw-cat',\n"
    if before.count(needle)!=1 or b'toddy-pw-cat' in before:raise ValueError('pipewire_tools_source_target_differs')
    alias_block=before.split(b'  pwcat_aliases = [\n',1)[1].split(b'  ]',1)[0]
    if tuple(re.findall(rb"'([^']+)'",alias_block))!=tuple(name.encode() for name in ALIASES):raise ValueError('pipewire_tools_upstream_aliases_changed')
    after=before.replace(needle,needle+b"    install_tag: 'toddy-pw-cat',\n")
    file.write_bytes(after)
    return {'path':'src/tools/meson.build','before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),
        'scope':'One install tag only; upstream tool sources/options and libraries unchanged'}


def source_members(members):
    names=set();expanded=0
    for member in members:
        parts=Path(member.name).parts
        if (not parts or parts[0]!='pipewire-1.6.8' or Path(member.name).is_absolute() or '..' in parts or member.name in names or
                not (member.isfile() or member.isdir() or member.issym())):raise ValueError('pipewire_tools_source_archive_namespace')
        names.add(member.name);expanded+=member.size if member.isfile() else 0
        if member.issym():
            if Path(member.linkname).is_absolute() or '..' in Path(member.linkname).parts:raise ValueError('pipewire_tools_source_archive_link')
    if not names or len(names)>30000 or expanded>128*1024**2:raise ValueError('pipewire_tools_source_archive_bound')
    return expanded


def baseline():
    record=regular(RECORDS/('pipewire_'+OLD+'_amd64.json'));archive=regular(CACHE/('pipewire_'+OLD+'_amd64.deb'))
    if digest(record)!=OLD_RECORD_SHA or digest(archive)!=OLD_ARCHIVE_SHA:raise ValueError('pipewire_tools_frozen_baseline_custody')
    value=json.loads(record.read_bytes())
    if value.get('name')!='pipewire' or value.get('version')!=OLD or value.get('installed') is not True or value.get('archive_sha256')!=OLD_ARCHIVE_SHA or not value.get('payload'):raise ValueError('pipewire_tools_frozen_baseline_record')
    # Read archive metadata with the builder's reader; no target path alias or
    # executable from that archive is used. Actual extract/install stays native.
    depends=subprocess.check_output(['/usr/bin/dpkg-deb','-f',str(archive),'Depends'],text=True,timeout=30).strip()
    if depends!=OLD_DEPENDS:raise ValueError('pipewire_tools_old_dependency_contract')
    return value,archive



def archive_summary(archive):
    """Authenticated archive metadata only; no extraction onto builder/host."""
    raw=subprocess.check_output(['/usr/bin/dpkg-deb','--ctrl-tarfile',str(archive)],timeout=30)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as control:
        seen=set()
        for member in control:
            name=str(Path(member.name))
            if member.isdir() and name=='.':continue
            if name not in ('control','md5sums','conffiles') or not member.isfile() or name in seen:raise ValueError('pipewire_tools_unreviewed_control_script')
            seen.add(name)
            if name=='conffiles' and control.extractfile(member).read().strip():raise ValueError('pipewire_tools_unreviewed_conffiles')
        if 'control' not in seen:raise ValueError('pipewire_tools_control_missing')
    raw=subprocess.check_output(['/usr/bin/dpkg-deb','--fsys-tarfile',str(archive)],timeout=30)
    if len(raw)>512*1024**2:raise ValueError('pipewire_tools_old_archive_expansion_bound')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as data:
        total=0;count=0
        for member in data:
            if Path(member.name).is_absolute() or '..' in Path(member.name).parts or not (member.isfile() or member.isdir() or member.issym() or member.islnk()):raise ValueError('pipewire_tools_old_archive_namespace')
            total+=member.size if member.isfile() else 0;count+=1
    return {'regular_bytes':total,'entries':count}


def verify_old(root,entries,exclusive=False):
    for virtual,row in entries.items():
        if not virtual.startswith('/') or '..' in Path(virtual).parts:raise ValueError('pipewire_tools_old_payload_path')
        path=root/virtual.lstrip('/');info=path.lstat()
        if (info.st_mode,info.st_uid,info.st_gid)!=(row['mode'],row['uid'],row['gid']):raise ValueError('pipewire_tools_old_payload_metadata_changed')
        if 'symlink' in row:
            if not path.is_symlink() or os.readlink(path)!=row['symlink']:raise ValueError('pipewire_tools_old_link_changed')
        elif 'sha256' in row:
            if path.is_symlink() or not path.is_file() or digest(path)!=row['sha256']:raise ValueError('pipewire_tools_old_bytes_changed')
        elif not row.get('directory') or not path.is_dir():raise ValueError('pipewire_tools_old_payload_kind')
    if exclusive:
        actual={'/'+p.relative_to(root).as_posix() for p in root.rglob('*')}
        if actual!=set(entries):raise ValueError('pipewire_tools_unselected_baseline_file')


def dependency_state():
    result={}
    for name,version in PROVIDERS.items():
        if native('/usr/bin/dpkg-query','-W','-f=${Status} ${Version}',name)!='install ok installed '+version:raise ValueError('pipewire_tools_native_provider_version')
        path=regular(RECORDS/(name+'_'+version+'_amd64.json'));value=json.loads(path.read_bytes())
        archive=regular(CACHE/(name+'_'+version+'_amd64.deb'))
        if not value.get('installed') or digest(archive)!=value['archive_sha256']:raise ValueError('pipewire_tools_native_provider_custody')
        result[name]={'version':version,'record_sha256':digest(path),'archive_sha256':digest(archive)}
    return result


def source_pins():
    names=(BUILD,INSTALL,CHECK,'scripts/build/phase2/pipewire_tools_native.py','scripts/build/phase2/isolated.sh')
    return {name:digest(regular(ROOT/name)) for name in names}


def prepare():
    fresh=(SOURCE,SOURCE.with_name(SOURCE.name+'-extracting'),WORK,STAGE,PREPARED,RECEIPT,PREPARED.with_suffix('.part'),RECEIPT.with_suffix('.part'),STAGE.with_name(STAGE.name+'-baseline.deb'),SOURCE_CUSTODY)
    fresh+=tuple(LOG.glob(JOB+'.*'))
    if any(os.path.lexists(path) for path in fresh):raise ValueError('pipewire_tools_preserve_existing_generation')
    for name in ('pw-cat',*ALIASES):
        if os.path.lexists(TARGET/'usr/bin'/name):raise ValueError('pipewire_tools_existing_unreviewed_tool')
    row,archive=baseline();archive_info=archive_summary(archive);dependencies=dependency_state();verify_old(TARGET,row['payload'])
    if native('/usr/bin/dpkg-query','-W','-f=${Conffiles}','pipewire'):raise ValueError('pipewire_tools_conffiles_require_explicit_review')
    # Protected custody is the first source write, retained on every failure.
    if shutil.disk_usage(LOG).free<SOURCE_BYTES+128*1024**2:raise ValueError('pipewire_tools_source_custody_capacity')
    upstream,custody=copy_frozen_source()
    with tarfile.open(upstream) as bundle:
        expanded=source_members(bundle.getmembers())
        if shutil.disk_usage(TARGET).free<16*1024**3+512*1024**2+8*expanded+3*archive_info['regular_bytes']:raise ValueError('pipewire_tools_16gib_reserve')
        state={'state':'preparing-no-replay','dependencies':dependencies,'inputs':source_pins(),'source_sha256':SOURCE_SHA,'expanded_source_bytes':expanded,
            'old_record_sha256':OLD_RECORD_SHA,'old_archive_sha256':OLD_ARCHIVE_SHA,'old_archive_storage':archive_info,'source_custody':custody}
        save(PREPARED,state);temporary=SOURCE.with_name(SOURCE.name+'-extracting');temporary.mkdir(mode=0o755)
        bundle.extractall(temporary,filter='data')
    (temporary/'pipewire-1.6.8').rename(SOURCE);temporary.rmdir();state['install_tag_patch']=patch_tag(SOURCE)
    shutil.copyfile(ROOT/BUILD,SOURCE/'toddy-pw-cat-build.sh');(SOURCE/'toddy-pw-cat-build.sh').chmod(0o444)
    for path in SOURCE.rglob('*'):
        if not path.is_symlink():path.chmod(0o555 if path.is_dir() or path.stat().st_mode&0o111 else 0o444)
    SOURCE.chmod(0o555);WORK.mkdir(mode=0o755);os.chown(WORK,101,101)
    state.update(state='prepared',source_inode=SOURCE.stat().st_ino,work_inode=WORK.stat().st_ino,source_manifest_sha256=inspect_stage(SOURCE)['manifest_sha256'])
    save(PREPARED,state)


def tool_stage(stage):
    observed=inspect_stage(stage);leaves={name:row for name,row in observed['entries'].items() if not row.get('directory')}
    expected={'usr/bin/pw-cat'}|{'usr/bin/'+name for name in ALIASES}
    if set(leaves)!=expected or leaves['usr/bin/pw-cat'].get('mode')!=0o755 or 'sha256' not in leaves['usr/bin/pw-cat']:raise ValueError('pipewire_tools_unselected_native_stage')
    for name in ALIASES:
        if leaves['usr/bin/'+name].get('symlink')!='pw-cat':raise ValueError('pipewire_tools_native_alias')
    return observed


def elf_dependencies(binary):
    with Path(binary).open('rb') as stream:header=stream.read(20)
    if len(header)!=20 or header[:6]!=b'\x7fELF\x02\x01' or header[18:20]!=b'\x3e\x00':raise ValueError('pipewire_tools_native_x86_64_ELF_required')
    from audit_native_elf import target_resolve
    dynamic=subprocess.check_output(['/usr/bin/readelf','-d',str(binary)],text=True)
    needed=re.findall(r'\((NEEDED|RPATH|RUNPATH)\).*\[(.*?)\]',dynamic);found=set()
    if not needed:raise ValueError('pipewire_tools_native_dynamic_ELF_required')
    for kind,soname in needed:
        if kind!='NEEDED' or '/' in soname:raise ValueError('pipewire_tools_native_RPATH_or_provider')
        path,canonical=target_resolve(TARGET,'/usr/lib/'+soname);owners=set()
        for listing in (TARGET/'var/lib/dpkg/info').glob('*.list'):
            if canonical in listing.read_text().splitlines() or '/usr/lib/'+soname in listing.read_text().splitlines():owners.add(listing.name.removesuffix('.list').split(':')[0])
        if len(owners)!=1 or not owners<=PROVIDERS.keys():raise ValueError('pipewire_tools_undeclared_native_ELF_owner')
        owner=next(iter(owners));record=json.loads((RECORDS/(owner+'_'+PROVIDERS[owner]+'_amd64.json')).read_bytes())
        if record['payload'].get(canonical,{}).get('sha256')!=digest(path):raise ValueError('pipewire_tools_provider_bytes_changed')
        found.add(owner)
    if not {'glibc','libsndfile','pipewire'}<=found:raise ValueError('pipewire_tools_required_direct_providers_missing')
    return {'direct_providers':sorted(found),'runtime_search_paths':False}


def qualify():
    prepared=json.loads(PREPARED.read_bytes())
    _,custody=verified_source()
    if prepared.get('source_custody')!=custody:raise ValueError('pipewire_tools_source_custody_changed')
    if (prepared['state']!='prepared' or prepared['inputs']!=source_pins() or prepared['dependencies']!=dependency_state() or
            SOURCE.stat().st_ino!=prepared['source_inode'] or WORK.stat().st_ino!=prepared['work_inode'] or
            inspect_stage(SOURCE)['manifest_sha256']!=prepared['source_manifest_sha256']):raise ValueError('pipewire_tools_prepared_inputs_changed')
    if (LOG/(JOB+'.exit')).read_text().strip()!='0':raise ValueError('pipewire_tools_isolated_job_not_complete')
    job=json.loads((LOG/(JOB+'.job.json')).read_bytes())
    expected=['/bin/bash',str(ROOT/'scripts/build/phase2/isolated.sh'),str(SOURCE),str(WORK),'bash','/src/toddy-pw-cat-build.sh']
    if job.get('command')!=expected or job.get('harness_sha256')!=prepared['inputs']['scripts/build/phase2/isolated.sh']:raise ValueError('pipewire_tools_wrong_isolated_job')
    observed=tool_stage(WORK/'stage');closure=elf_dependencies(WORK/'stage/usr/bin/pw-cat')
    proof=json.loads((WORK/'tool-qualified.json').read_bytes())
    if proof.get('target')!='src/tools/pw-cat' or proof.get('install_tag')!='toddy-pw-cat' or proof.get('upstream')!='1.6.8' or proof.get('help_exit')!=0 or proof.get('aliases')!=list(ALIASES) or proof.get('options')!={'pw-cat':'enabled','sndfile':'enabled','pw-cat-ffmpeg':'disabled'}:raise ValueError('pipewire_tools_native_help_not_proven')
    return prepared,observed,closure



def verify_additions(root,old_entries):
    allowed=set(old_entries)|{'/usr/bin/pw-cat'}|{'/usr/bin/'+name for name in ALIASES}|{'/usr/share/doc/pipewire/pw-cat-upgrade-source.json'}
    actual={'/'+path.relative_to(root).as_posix() for path in root.rglob('*') if not path.is_relative_to(root/'DEBIAN')}
    if actual!=allowed:raise ValueError('pipewire_tools_unselected_merged_stage')
    verify_old(root,old_entries)


def transaction(phase):
    marker=json.loads((Path('/var/log/toddy/build')/(STEP+'.running.json')).read_bytes())
    if marker.get('step')!=STEP or marker.get('user')!='root' or marker.get('recipe_sha256')!=digest(ROOT/INSTALL) or marker.get('postcheck_sha256')!=digest(ROOT/CHECK):raise ValueError('pipewire_tools_root_dispatcher_required')
    if phase=='install' and marker.get('recipe_pid') not in (os.getpid(),os.getppid()):raise ValueError('pipewire_tools_dispatcher_pid')
    if phase=='postcheck' and (type(marker.get('recipe_exit')) is not int or marker['recipe_exit']!=0):raise ValueError('pipewire_tools_recipe_not_complete')


def install():
    from dependency_preflight import native as check_dependencies
    transaction('install');prepared,tools,closure=qualify();old,archive=baseline();verify_old(TARGET,old['payload']);check_dependencies(DEPENDS)
    for name in ('pw-cat',*ALIASES):
        if os.path.lexists(TARGET/'usr/bin'/name):raise ValueError('pipewire_tools_existing_unreviewed_tool')
    if any(os.path.lexists(p) for p in (STAGE,RECEIPT,CACHE/('pipewire_'+VERSION+'_amd64.deb'),RECORDS/('pipewire_'+VERSION+'_amd64.json'))):raise ValueError('pipewire_tools_existing_promotion_no_replay')
    archive_info=archive_summary(archive)
    size=archive_info['regular_bytes']+sum(row.get('bytes',0) for row in tools['entries'].values())
    if shutil.disk_usage(TARGET).free<16*1024**3+512*1024**2+3*size:raise ValueError('pipewire_tools_16gib_reserve')
    # Native extraction from a verified old archive; no dirty installed-root copy.
    incoming=STAGE.with_name(STAGE.name+'-baseline.deb')
    if os.path.lexists(incoming):raise ValueError('pipewire_tools_existing_baseline_copy')
    shutil.copyfile(archive,incoming);incoming.chmod(0o644)
    if digest(incoming)!=OLD_ARCHIVE_SHA:raise ValueError('pipewire_tools_baseline_copy_changed')
    native('/usr/bin/dpkg-deb','--extract','/'+incoming.relative_to(TARGET).as_posix(),'/'+STAGE.relative_to(TARGET).as_posix())
    verify_old(STAGE,old['payload'],exclusive=True)
    for relative,row in tools['entries'].items():
        if row.get('directory'):continue
        source=WORK/'stage'/relative;destination=STAGE/relative
        if os.path.lexists(destination):raise ValueError('pipewire_tools_old_namespace_collision')
        if 'symlink' in row:os.symlink(row['symlink'],destination)
        else:shutil.copyfile(source,destination);destination.chmod(row['mode'])
    verify_old(STAGE,old['payload'])
    manifest={'package':'pipewire','version':VERSION,'upstream':'1.6.8','old_payload_entries_preserved':len(old['payload']),
        'old_archive_sha256':OLD_ARCHIVE_SHA,'old_record_sha256':OLD_RECORD_SHA,'source_sha256':SOURCE_SHA,
        'source_inputs':source_pins(),'source_custody':prepared['source_custody'],'patch':prepared['install_tag_patch'],'tools':tools,'closure':closure,
        'scope':'Unchanged old libraries/configs; native help only, real audio process qualification pending'}
    doc=STAGE/'usr/share/doc/pipewire/pw-cat-upgrade-source.json';save(doc,manifest);doc.chmod(0o644)
    verify_additions(STAGE,old['payload'])
    save(RECEIPT,{'state':'native-install-intended','manifest':manifest})
    subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),'pipewire',VERSION,str(STAGE),'--source',ARCHIVE,
        '--recipe',INSTALL,'--depends',DEPENDS,'--compression-threads','2','--install'],cwd=ROOT,check=True,close_fds=True)
    save(RECEIPT,{'state':'native-installed-postcheck-pending','manifest':manifest})


def postcheck():
    transaction('postcheck');_,custody=verified_source();receipt=json.loads(RECEIPT.read_bytes())
    if receipt['state']!='native-installed-postcheck-pending' or receipt['manifest']['source_inputs']!=source_pins() or receipt['manifest'].get('source_custody')!=custody:raise ValueError('pipewire_tools_install_requires_reconciliation')
    if native('/usr/bin/dpkg-query','-W','-f=${Status} ${Version}','pipewire')!='install ok installed '+VERSION:raise ValueError('pipewire_tools_upgraded_native_version')
    old,archive=baseline();verify_old(TARGET,old['payload']);verify_additions(STAGE,old['payload']);tool_stage(WORK/'stage');elf_dependencies(TARGET/'usr/bin/pw-cat')
    for name in ('pw-cat',*ALIASES):
        staged=STAGE/'usr/bin'/name;installed=TARGET/'usr/bin'/name
        if staged.is_symlink():
            if not installed.is_symlink() or os.readlink(installed)!='pw-cat':raise ValueError('pipewire_tools_installed_alias')
        elif installed.is_symlink() or digest(installed)!=digest(staged):raise ValueError('pipewire_tools_installed_binary_changed')
        info=installed.lstat()
        if info.st_uid or info.st_gid or stat.S_IMODE(info.st_mode)!=stat.S_IMODE(staged.lstat().st_mode):raise ValueError('pipewire_tools_installed_tool_metadata')
        output=native('/usr/bin/timeout','--kill-after=2','15','/usr/bin/'+name,'--help')
        if not output:raise ValueError('pipewire_tools_installed_help_consumer')
    version=native('/usr/bin/timeout','--kill-after=2','15','/usr/bin/pw-cat','--version')
    if 'Compiled with libpipewire 1.6.8' not in version or 'Linked with libpipewire 1.6.8' not in version:raise ValueError('pipewire_tools_native_SDK_or_linked_version')
    if native('/usr/bin/dpkg-query','-W','-f=${Conffiles}','pipewire') or native('/usr/bin/dpkg','--audit'):raise ValueError('pipewire_tools_database_or_conffile_drift')
    native('/usr/bin/apt-get','check')
    current=json.loads(regular(RECORDS/('pipewire_'+VERSION+'_amd64.json')).read_bytes())
    new_archive=regular(CACHE/('pipewire_'+VERSION+'_amd64.deb'))
    if current.get('installed') is not True or current.get('archive_sha256')!=digest(new_archive) or current.get('version')!=VERSION:raise ValueError('pipewire_tools_new_archive_custody')
    if any(current['payload'].get(path)!=row for path,row in old['payload'].items()):raise ValueError('pipewire_tools_new_record_changed_baseline')
    expected=set(old['payload'])|{'/usr/bin/pw-cat'}|{'/usr/bin/'+name for name in ALIASES}|{'/usr/share/doc/pipewire/pw-cat-upgrade-source.json'}
    if set(current['payload'])!=expected:raise ValueError('pipewire_tools_new_package_unselected_payload')
    receipt.update(state='native-tool-package-verified',old_payload_unchanged=True,actual_audio_process_qualification='pending')
    save(RECEIPT,receipt)


def main():
    if os.getuid()!=0 or os.geteuid()!=0 or len(sys.argv)!=2 or sys.argv[1] not in ('prepare','qualify','install','postcheck'):raise SystemExit('pipewire_tools_guest_root_coordinator_required')
    subprocess.run(['/bin/bash','-c','source "$1"; guard_target','guard',str(ROOT/'scripts/build/target.sh')],check=True)
    LOG.mkdir(parents=True,exist_ok=True)
    if sys.argv[1]=='prepare':
        fd=os.open('/var/log/toddy/build/build.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if list(Path('/var/log/toddy/build').glob('*.running.json')):raise ValueError('pipewire_tools_other_native_transaction')
            prepare()
        finally:os.close(fd)
    elif sys.argv[1]=='qualify':print(json.dumps(qualify()[2],sort_keys=True))
    elif sys.argv[1]=='install':install()
    else:postcheck()

if __name__=='__main__':main()
