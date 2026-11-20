#!/usr/bin/env python3
"""Fixed candidate and historical root custody profiles; no arbitrary paths.

Offline after real matching finalizer2; live before fresh finalizer2 only from
completed resource candidate and exact independently reviewed protected inputs.
No generic path/cleanup flag.
"""
import base64,errno,fcntl,grp,hashlib,json,os,re,shutil,stat,subprocess,sys
from contextlib import contextmanager
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs')
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[3])]
import candidate_root_archive as archive
from runtime.installer.composition import secured as composition_secured,validate_finalizer_report
from runtime.installer.native_finalizer import payload_module
from image_assemble import unclosed_compiler_jobs,ReviewedInputs
PROFILES={'offline':('toddy-offline-image-1','toddy-offline-image-2','offline-root-2','toddy-installer-native-inputs'),
          'live':('toddy-live-image-1','toddy-live-image-2','live-root-2','toddy-live-native-inputs'),
          'mvp-offline':('toddy-mvp-offline-image-1','toddy-mvp-offline-image-2','mvp-offline-root-2','toddy-mvp-installer-native-inputs'),
          'mvp-live':('toddy-mvp-live-image-9','toddy-mvp-live-image-9-reviewed','mvp-live-root-2','toddy-mvp-live-native-inputs-4'),
          'mvp-live-failed1':('toddy-mvp-live-image-1','toddy-mvp-live-image-2','mvp-live-root-2','toddy-mvp-live-native-inputs'),
          'mvp-live-failed3':('toddy-mvp-live-image-3','toddy-mvp-live-image-2','mvp-live-root-2','toddy-mvp-live-native-inputs'),
          'mvp-live-failed4':('toddy-mvp-live-image-4','toddy-mvp-live-image-2','mvp-live-root-2','toddy-mvp-live-native-inputs-2'),
          'mvp-live-failed5':('toddy-mvp-live-image-5','toddy-mvp-live-image-2','mvp-live-root-2','toddy-mvp-live-native-inputs-3')}


HISTORICAL={'h10-expanded':('h10-live-root',8707435,1794055093154113811,'h10'),
            'h11-expanded':('h11-release-root',1239394,1794056902695122701,'h11')}


def configure(profile):
    global PROFILE,WORK,ARTIFACT,REVIEWED,FINAL_ROOT,INPUTS,CUSTODY,STATE,VIRTUAL
    if profile in ('mvp-live-stage6','mvp-live-stage7','mvp-live-stage8'):
        PROFILE=profile
        name='toddy-mvp-live-image-2' if profile=='mvp-live-stage6' else ('toddy-mvp-live-image-7-reviewed' if profile=='mvp-live-stage7' else 'toddy-mvp-live-image-8-reviewed')
        WORK=TARGET/'sources/stage'/name;ARTIFACT=WORK/'mvp-live-root-2'
        REVIEWED=WORK;FINAL_ROOT=ARTIFACT;INPUTS=TARGET/'sources/stage/toddy-mvp-live-native-inputs-4'
        CUSTODY=WORK/(profile.removeprefix('mvp-live-')+'-root-custody-1');STATE=CUSTODY/'custody.json'
        VIRTUAL='/sources/stage/'+name+'/mvp-live-root-2'
        return
    if profile in HISTORICAL:
        PROFILE=profile;name,_inode,_mtime,_proof=HISTORICAL[profile]
        WORK=TARGET/'sources/stage';ARTIFACT=WORK/name;REVIEWED=FINAL_ROOT=INPUTS=None
        CUSTODY=WORK/(profile+'-root-custody-1');STATE=CUSTODY/'custody.json';VIRTUAL='/sources/stage/'+name
        return
    if profile not in PROFILES:raise ValueError('candidate_root_custody_unknown_fixed_profile')
    PROFILE=profile;candidate,reviewed,final,inputs=PROFILES[profile]
    WORK=TARGET/'sources/stage'/candidate;ARTIFACT=WORK/'root';REVIEWED=TARGET/'sources/stage'/reviewed
    FINAL_ROOT=REVIEWED/final;INPUTS=TARGET/'sources/stage'/inputs;CUSTODY=WORK/'root-custody-1';STATE=CUSTODY/'custody.json'
    VIRTUAL='/sources/stage/'+candidate+'/root'


configure('offline')
LOG=Path('/var/log/toddy/phase2');LOCK=Path('/var/log/toddy/build/build.lock')


def secured(path,limit=256*1024*1024):
    path=Path(path)
    if not path.is_relative_to('/var/log/toddy'):
        return composition_secured(path,limit)
    if not path.is_absolute() or path.resolve()!=path:raise ValueError('candidate_root_custody_log_redirect')
    for parent in path.parents:
        info=parent.lstat()
        exception=(parent==Path('/var/log') and info.st_uid==0 and
            info.st_gid==grp.getgrnam('syslog').gr_gid and stat.S_IMODE(info.st_mode)==0o775)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid or (info.st_mode&0o022 and not exception):
            raise ValueError('candidate_root_custody_log_parent')
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid or info.st_gid or info.st_nlink!=1 or info.st_mode&0o022 or info.st_size>limit:
        raise ValueError('candidate_root_custody_log_file')
    return path


def read(path,limit=128*1024**2):return payload_module().strict(secured(path,limit).read_bytes())

def save(path,value):
    part=path.with_suffix('.part')
    with part.open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(archive.encoded(value));stream.flush();os.fsync(stream.fileno())
    os.replace(part,path);fsync(path.parent)

def fsync(path):
    fd=os.open(path,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def private(path,mode):
    info=path.lstat()
    if path.resolve()!=path or not stat.S_ISDIR(info.st_mode) or info.st_uid or info.st_gid or stat.S_IMODE(info.st_mode)!=mode or info.st_dev!=TARGET.stat().st_dev:raise ValueError('candidate_root_custody_directory')
    return info


def no_mounts():
    prefixes=(str(ARTIFACT),VIRTUAL)
    device=ARTIFACT.stat().st_dev;wanted=(os.major(device),os.minor(device))
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:lines=(process/'mountinfo').read_text().splitlines()
        except (FileNotFoundError,ProcessLookupError):continue
        for line in lines:
            fields=line.split();major,minor=map(int,fields[2].split(':'))
            if (major,minor)!=wanted:continue
            for value in (fields[3],fields[4]):
                if any(value==prefix or value.startswith(prefix+'/') for prefix in prefixes):raise ValueError('candidate_root_custody_mount_consumer')


def no_consumers(snapshot):
    wanted={(row['device'],row['inode']) for row in snapshot['identities'].values()}
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():continue
        try:descriptors=[process/'cwd',process/'root',*list((process/'fd').iterdir())]
        except (FileNotFoundError,ProcessLookupError):continue
        for descriptor in descriptors:
            try:info=descriptor.stat()
            except (FileNotFoundError,ProcessLookupError):continue
            if (info.st_dev,info.st_ino) in wanted:raise ValueError('candidate_root_custody_open_consumer')
        try:lines=(process/'maps').read_text().splitlines()
        except (FileNotFoundError,ProcessLookupError):continue
        for line in lines:
            fields=line.split(None,5);major,minor=(int(value,16) for value in fields[3].split(':'))
            if (os.makedev(major,minor),int(fields[4])) in wanted:raise ValueError('candidate_root_custody_mapped_consumer')
    for marker in Path('/sys/block').glob('loop*/loop/backing_file'):
        value=marker.read_text().strip()
        if value:
            path=Path('/'+value.lstrip('/'))
            if path==ARTIFACT or path.is_relative_to(ARTIFACT) or path==Path(VIRTUAL) or path.is_relative_to(VIRTUAL):raise ValueError('candidate_root_custody_loop_consumer')
    no_mounts()



def preserved_link(path,tree):
    """Inspect raw relative targets without traversing outside the retained tree."""
    path=Path(path);tree=Path(tree)
    if tree.resolve()!=tree or path.parent.resolve()!=path.parent or not path.is_relative_to(tree):raise ValueError('historical_expanded_redirected_preserved_link')
    info=path.lstat()
    if not stat.S_ISLNK(info.st_mode):raise ValueError('historical_expanded_preserved_link_type')
    raw=os.readlink(os.fsencode(path))
    if raw.startswith(b'/'):raise ValueError('historical_expanded_absolute_preserved_link')
    pending=os.fsdecode(raw).split('/');current=path.parent;links=0
    while pending:
        part=pending.pop(0)
        if part in ('','.'):continue
        if part=='..':
            if current==tree:raise ValueError('historical_expanded_preserved_link_escape')
            current=current.parent;continue
        candidate=current/part
        try:entry=candidate.lstat()
        except OSError as error:raise ValueError('historical_expanded_preserved_link_missing') from error
        if stat.S_ISLNK(entry.st_mode):
            links+=1
            if links>64:raise ValueError('historical_expanded_preserved_link_cycle')
            target=os.readlink(os.fsencode(candidate))
            if target.startswith(b'/'):raise ValueError('historical_expanded_absolute_preserved_link')
            pending=os.fsdecode(target).split('/')+pending
        else:
            current=candidate
            if pending and not stat.S_ISDIR(entry.st_mode):raise ValueError('historical_expanded_preserved_link_parent')
    if not current.is_relative_to(tree):raise ValueError('historical_expanded_preserved_link_escape')
    return {'type':'symlink','tree':str(tree),'target_base64':base64.b64encode(raw).decode('ascii'),
        'target_sha256':hashlib.sha256(raw).hexdigest(),'mode':info.st_mode,'uid':info.st_uid,'gid':info.st_gid,
        'device':info.st_dev,'inode':info.st_ino,'nlink':info.st_nlink,'mtime_ns':info.st_mtime_ns,'ctime_ns':info.st_ctime_ns,
        'xattrs':{name:base64.b64encode(os.getxattr(path,name,follow_symlinks=False)).decode('ascii') for name in sorted(os.listxattr(path,follow_symlinks=False))}}


def historical_eligible():
    """Only two original expanded caches; frozen evidence, not new acceptance."""
    import opaque_tar_profiles
    name,inode,mtime,proof=HISTORICAL[PROFILE];config=opaque_tar_profiles.profile(proof)
    private(WORK,0o755);info=private(ARTIFACT,0o755)
    if (info.st_dev,info.st_ino,info.st_mtime_ns)!=(64788,inode,mtime):raise ValueError('historical_expanded_frozen_root_identity')
    evidence=WORK/config['evidence'];preserved={};preserved_links={}
    for leaf,expected in (('assembly.json',config['assembly_sha256']),(config['manifest'],config['manifest_sha256'])):
        path=secured(evidence/leaf)
        if archive.sha(path)!=expected:raise ValueError('historical_expanded_frozen_evidence_changed')
    # Recheck every original byte, mode, UID/GID, mtime, xattr and link class.
    # Raw xattrs/ACLs are separately retained and verified by the custody archive.
    image=archive.snapshot(ARTIFACT)
    entries={name:{**row,'xattrs':{key:hashlib.sha256(base64.b64decode(value,validate=True)).hexdigest()
        for key,value in row['xattrs'].items()}} for name,row in image['entries'].items()}
    for row in entries.values():
        if 'symlink' in row:row['symlink']=Path(row['symlink']).as_posix()
    original=read(evidence/config['manifest'])
    if {'entries':entries,'hardlink_groups':image['hardlink_groups']}!=original:raise ValueError('historical_expanded_original_full_image_differs')
    # Preserve evidence and all media bytes; only ARTIFACT can be removed.
    media=WORK/('h10-live-media' if proof=='h10' else 'h11-release-media')
    for directory in (evidence,media):
        if directory.resolve()!=directory or not directory.is_dir():raise ValueError('historical_expanded_retained_evidence_media_required')
        for path in sorted(directory.rglob('*')):
            if path.is_symlink():preserved_links[str(path)]=preserved_link(path,directory)
            elif path.is_file():preserved[str(path)]=archive.sha(secured(path,8*1024**3))
    for path in (Path(__file__),Path(archive.__file__),Path(opaque_tar_profiles.__file__),ROOT/'scripts/build/phase2/image_native.sh'):
        preserved[str(path)]=archive.sha(secured(path))
    no_mounts()
    return {'profile':PROFILE,'root_identity':[info.st_dev,info.st_ino,info.st_mtime_ns],
        'preserved':preserved,'preserved_links':preserved_links,'original_image_manifest_sha256':config['manifest_sha256'],
        'scope':'Frozen historical expanded duplicate only; foundation CLI consumers retired; original evidence/media/backings/ISOs retained',
        'foundation_rebuild_authorized':False,'new_acceptance_claimed':False,
        'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def eligible():
    """Fixed workflow boundary; full archive metadata proof remains separate."""
    if PROFILE in HISTORICAL:return historical_eligible()
    if PROFILE=='mvp-live-stage8':return observer_stage8_eligible()
    if PROFILE in ('mvp-live-stage6','mvp-live-stage7'):return failed_stage_eligible()
    if PROFILE in ('mvp-live-failed1','mvp-live-failed3','mvp-live-failed4','mvp-live-failed5'):return failed_live_eligible()
    p=payload_module();work=private(WORK,0o700);root=private(ARTIFACT,0o755)
    pin=[root.st_dev,work.st_ino,root.st_ino]
    unpack=read(WORK/'unpacked.json');intent=read(WORK/'unpack-intent.json');candidate=read(WORK/'candidate-resource-receipt.json')
    # Same recheck as finalize_native, using the fixed builder view of its input
    # directory; no source path/callback is accepted from a request or document.
    inputs=object.__new__(ReviewedInputs);inputs.kind={'offline':'base','live':'live','mvp-offline':'mvp-base','mvp-live':'mvp-live'}[PROFILE];inputs.base=INPUTS;inputs.bundle=INPUTS/'payload';inputs.recheck()
    manifest=inputs.manifest;manifest_sha=inputs.pins['payload/manifest.json'];descriptor=inputs.descriptor
    if (unpack.get('state')!='native-archives-unpacked-needs-resource-qualification' or intent.get('state')!='unpack-intended' or
            unpack.get('assembly_pin')!=pin or intent.get('assembly_pin')!=pin or unpack.get('root')!=VIRTUAL or intent.get('root')!=VIRTUAL or
            unpack.get('manifest_sha256')!=manifest_sha or intent.get('manifest_sha256')!=manifest_sha or
            unpack.get('dpkg_log_sha256')!=archive.sha(secured(WORK/'dpkg.log')) or
            candidate.get('state')!='native-candidate-awaiting-independent-review' or candidate.get('blockers')!=[] or
            candidate.get('manifest_sha256')!=manifest_sha or candidate.get('root_inode')!=root.st_ino or candidate.get('root_device')!=root.st_dev):
        raise ValueError('candidate_root_custody_completed_resource_generation_required')
    maps={'candidate-generated-entries.json':'generated-entries.json','candidate-clean-image-manifest.json':'expected-image-manifest.json'}
    for old,new in maps.items():
        if archive.sha(secured(WORK/old))!=archive.sha(secured(INPUTS/new)):raise ValueError('candidate_root_custody_independent_review_binding')
    if (candidate.get('generated_entries_sha256')!=archive.sha(WORK/'candidate-generated-entries.json') or
            candidate.get('candidate_image_manifest_sha256')!=archive.sha(WORK/'candidate-clean-image-manifest.json') or
            candidate.get('policy_sha256')!=descriptor['policy_sha256']):raise ValueError('candidate_root_custody_reviewed_resource_outputs_changed')
    checks={};final_pin=None;trees=[ARTIFACT]
    paths=[WORK/name for name in ('unpacked.json','unpack-intent.json','resource-intent.json','candidate-resource-receipt.json','candidate-generated-entries.json','candidate-clean-image-manifest.json','dpkg.log')]
    if PROFILE in ('offline','mvp-offline'):
        reviewed=private(REVIEWED,0o700);final=private(FINAL_ROOT,0o755);final_pin=[final.st_dev,reviewed.st_ino,final.st_ino]
        finished=read(REVIEWED/'finalized.json')
        if (finished.get('state')!='native-finalizer-verified' or finished.get('root')!='/'+str(FINAL_ROOT.relative_to(TARGET)) or
                finished.get('assembly_pin')!=final_pin or finished.get('payload_manifest_sha256')!=manifest_sha or
                finished.get('production_ready') is not False or finished.get('native_boot_verified') is not False or
                finished.get('source_sha256')!=inputs.source_hashes or set(finished.get('checks',{}))!=set(p.CHECKS) or
                finished.get('policy_sha256')!=descriptor['policy_sha256'] or finished.get('generated_entries_sha256')!=inputs.pins['generated-entries.json'] or
                finished.get('image_manifest_sha256')!=descriptor['image_manifest_sha256']):raise ValueError('candidate_root_custody_actual_finalizer2_required')
        for name,row in finished['checks'].items():
            virtual='/run/toddy-installer/finalization-'+FINAL_ROOT.name+'/'+name+'.json';report=TARGET/virtual.lstrip('/')
            if set(row)!={'passed','exit_status','report','report_sha256'} or row['passed'] is not True or type(row['exit_status']) is not int or row['exit_status']!=0 or row['report']!=virtual or archive.sha(secured(report))!=row['report_sha256']:raise ValueError('candidate_root_custody_actual_finalizer_report')
            validate_finalizer_report(read(report),name,descriptor);checks[name]=row['report_sha256']
        paths.extend((REVIEWED/'finalized.json',REVIEWED/'finalize-intent.json'));trees.append(FINAL_ROOT)
    else:
        # This explicit capacity boundary precedes fresh generation2. No partial
        # reviewed root, synthetic finalizer receipt or old-tree adoption allowed.
        if os.path.lexists(REVIEWED):raise ValueError('candidate_root_custody_live2_exists_reconcile_first')
    for tree in trees:
        current=p.PreparedPayload.audit_tree(tree,manifest,inputs.generated)
        if hashlib.sha256(p.encoded(current)).hexdigest()!=descriptor['image_manifest_sha256']:raise ValueError('candidate_root_custody_current_reviewed_image_required')
    paths.extend(INPUTS/name for name in ('policy.json','generated-entries.json','expected-image-manifest.json','boot-profile.json'))
    paths.extend(path for path in inputs.bundle.rglob('*') if path.is_file())
    paths.extend(ROOT/'scripts/build/phase2'/name for name in ('image_assemble.py','resource_recipe.py','image_native.sh'))
    preserved={str(path):archive.sha(secured(path)) for path in paths}
    inputs.recheck();no_mounts()
    return {'profile':PROFILE,'assembly_pin':pin,'final_assembly_pin':final_pin,'descriptor':descriptor,'preserved':preserved,
        'reviewed_input_pins':inputs.pins,'finalizer_reports_sha256':checks,'source_sha256':inputs.source_hashes,
        'finalizer2_performed':PROFILE in ('offline','mvp-offline'),'workflow_boundary':'actual-offline-finalizer2' if PROFILE in ('offline','mvp-offline') else 'reviewed-live-inputs-before-fresh-finalizer2',
        'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def failed_live_eligible():
    """Archive an exact uncertain MVP root without accepting or replaying it."""
    work=private(WORK,0o700);root=private(ARTIFACT,0o755)
    pin=[root.st_dev,work.st_ino,root.st_ino]
    unpack=read(WORK/'unpacked.json');intent=read(WORK/'unpack-intent.json');resource=read(WORK/'resource-intent.json')
    if (unpack.get('state')!='native-archives-unpacked-needs-resource-qualification' or
            intent.get('state')!='unpack-intended' or
            unpack.get('assembly_pin')!=pin or intent.get('assembly_pin')!=pin or
            unpack.get('root')!=VIRTUAL or intent.get('root')!=VIRTUAL or
            unpack.get('manifest_sha256')!=intent.get('manifest_sha256') or
            resource.get('kind')!='unqualified-native-resource-candidate' or
            resource.get('root_device')!=root.st_dev or resource.get('root_inode')!=root.st_ino or
            resource.get('manifest_sha256')!=unpack['manifest_sha256'] or
            resource.get('production_ready') is not False or
            (PROFILE=='mvp-live-failed1' and not all((WORK/name).is_file() for name in (
                'resource-directory-recovery-intent.json','resource-account-recovery-intent2.json'))) or
            (PROFILE=='mvp-live-failed4' and not (WORK/'resource-command-failure.json').is_file()) or
            (PROFILE!='mvp-live-failed5' and any(os.path.lexists(WORK/name) for name in ('candidate-resource-receipt.json','candidate-generated-entries.json','candidate-clean-image-manifest.json')))):
        raise ValueError('candidate_root_custody_exact_uncertain_live_required')
    if PROFILE=='mvp-live-failed5':
        candidate=read(WORK/'candidate-resource-receipt.json')
        if (candidate.get('state')!='blocked-native-output-review' or
                candidate.get('root_device')!=root.st_dev or candidate.get('root_inode')!=root.st_ino or
                candidate.get('manifest_sha256')!=unpack['manifest_sha256'] or
                candidate.get('blockers')!=[{'path':'/usr/share/icons/Adwaita/icon-theme.cache',
                                              'reason':'owned-output-differs-requires-native-record-requalification'}] or
                not all((WORK/name).is_file() for name in ('candidate-generated-entries.json','candidate-clean-image-manifest.json'))):
            raise ValueError('candidate_root_custody_exact_blocked_live5_required')
    paths=[WORK/name for name in ('unpacked.json','unpack-intent.json','resource-intent.json','dpkg.log')]
    if (WORK/'resource-command-failure.json').exists():paths.append(WORK/'resource-command-failure.json')
    if PROFILE=='mvp-live-failed1':paths.extend(WORK/name for name in (
        'resource-directory-recovery-intent.json','resource-account-recovery-intent2.json'))
    if PROFILE=='mvp-live-failed5':paths.extend(WORK/name for name in ('candidate-resource-receipt.json','candidate-generated-entries.json','candidate-clean-image-manifest.json'))
    paths.extend(INPUTS/name for name in ('input-prepared.json','policy.json','payload/manifest.json'))
    paths.extend((ROOT/'scripts/build/phase2/image_native.sh',ROOT/'scripts/build/phase2/candidate_root_custody.py'))
    preserved={str(path):archive.sha(secured(path)) for path in paths}
    no_mounts()
    return {'profile':PROFILE,'assembly_pin':pin,'preserved':preserved,
        'workflow_boundary':'uncertain-'+PROFILE+'-root-archival-only-no-resource-acceptance',
        'root_retirement_only_after_complete_private_host_proof':True,
        'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def failed_stage_eligible():
    """Retire only the partial live transform after full private archive proof."""
    work=private(WORK,0o700);root=private(ARTIFACT,0o755)
    pin=[root.st_dev,work.st_ino,root.st_ino]
    finalized=read(WORK/'finalized.json');intent=read(WORK/'live-profile-intent.json')
    expected_source={'mvp-live-stage6':'c4e55e7289cea15875cafed6b0ab51fbacef945ff842da57d27526bf22b81de1',
                     'mvp-live-stage7':'580826999688c055841cb7d406b23585b80373c1b8eea410907f58abe6600269'}[PROFILE]
    dconf=ARTIFACT/'etc/dconf/db/toddy-live'
    failed_output=(ARTIFACT/'etc/dconf/db/ibus').is_file() if PROFILE=='mvp-live-stage6' else (
        dconf.is_file() and stat.S_IMODE(dconf.stat().st_mode)==0o600 and dconf.stat().st_uid==0)
    if (finalized.get('state')!='native-finalizer-verified' or finalized.get('root')!=VIRTUAL or
            finalized.get('assembly_pin')!=pin or
            intent.get('kind')!='source-attributed-live-transform' or
            intent.get('base_image_manifest_sha256')!=finalized.get('image_manifest_sha256') or
            intent.get('source_sha256')!=expected_source or
            os.path.lexists(WORK/'live-profile-receipt.json') or
            not failed_output):
        raise ValueError('candidate_root_custody_exact_partial_stage6_required')
    paths=[WORK/name for name in ('adoption-intent.json','adopted.json','finalize-intent.json','finalized.json',
                                   'synthetic-reset-intent.json','live-profile-intent.json')]
    paths.extend(INPUTS/name for name in ('input-prepared.json','policy.json','payload/manifest.json',
                                           'generated-entries.json','expected-image-manifest.json'))
    paths.extend((ROOT/'scripts/build/phase2/image_native.sh',ROOT/'scripts/build/phase2/candidate_root_custody.py',
                  ROOT/'scripts/build/phase2/live_profile.py'))
    preserved={str(path):archive.sha(secured(path)) for path in paths}
    no_mounts()
    return {'profile':PROFILE,'assembly_pin':pin,'preserved':preserved,
        'workflow_boundary':'partial-'+PROFILE+'-root-archival-only-no-media-or-boot-acceptance',
        'root_retirement_only_after_complete_private_host_proof':True,
        'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}



# Exact retained observer-drift boundary; these hashes are archival provenance,
# never permission to accept, repair or replay an image generation.
STAGE8_PIN=[64788,11562326,10943709]
STAGE8_ENTRY_COUNTS=(150294,150298)
STAGE8_FAILURE_SHA='8b073a085ccf53cfec4baac26f4ba8510c7e72006bbc491eadb4daf12962652e'
STAGE8_LIVE_SOURCE='1e2329a179ec55592a683e21e397def916809853244821c5539e5590fd71926f'
STAGE8_FROZEN={'acl-report.json': '95d815bea4d12ef7fe7128331dd123d97ed4b2e46db327e39b817c7cd6f6c50a',
 'adopted.json': '42ea401fe6ba73de0937c5d24e1d8bfe2f3aee93cadfa611170e604beed7f610',
 'adoption-intent.json': '8677afda4458fa2a6b1c61224e5ef43d98fe41dc5e1873ee271a229b2b3186b5',
 'evidence/assembly.json': '49d9ff60ad0065ac28cc38d70b3970ea1eda6574261b21f5c6ffc88e3d5b09d6',
 'evidence/image-manifest.json': 'bd5c3f319af634949d3a2fe2433095a60c23d7145d5cf4c547479491a44af93e',
 'finalize-intent.json': 'f1d8ba4ada4d5670c8aa38b47dac7db1c1959db7ff9d8b2632ce00d03fb2ede4',
 'finalized.json': 'dcf94bffd2255752628b32ea6993f52a15f4a9c0c830fe27fcaabe66bcd2233a',
 'live-image-manifest.json': 'f9c138fdb5204a470581c5e5c574512f15d946c795d5907a28ecbe38c8f94fdd',
 'live-profile-intent.json': '7773d9f6628934c112285c1c90f541bd4f84e50de08d35cc7f89db9688b3e454',
 'live-profile-receipt.json': 'cacf5c989e48d5d1c87b386514239c1df08a2bf02f3acf17c7c1fe3397ef6e5d',
 'synthetic-reset-intent.json': '56fb012f5812f351e439d2a0f0cfbef9aed3fc6976fdf6ef11cd4b543d0d6b16'}
STAGE8_SOURCE_JOURNALS={'candidate-clean-image-manifest.json': 'fcdd70749575fc562fddc007d9a38f8f92d09fd16eb0ae34421737cdd2eb5941',
 'candidate-generated-entries.json': '93b6042c5f3cae9ee0dff2142182e9729f32537f646acf7b9fc15c4bdb33af26',
 'candidate-resource-receipt.json': '544adf813323a12297bbf8833d1f786057271b96b163ff7c0b7ff6068a11a548',
 'dpkg.log': '10bd0b89bdd51fd984748391894f22b994597c932cca0a576658b737b71250ba',
 'resource-intent.json': 'eefc5315e085ce6abe582d72b4dbaf63ab94f81a986ae9ee6c6b23c2b03eeac2',
 'unpack-intent.json': 'db146d5b332de193d03f327a528f5b32d8ce82bcd63ce08e339303ca254d2850',
 'unpacked.json': '2eb754381f3bfbff1eec779fb50103a71d8130d8262cae283b733903e9b1be31'}
STAGE8_DCONF_STATE={
    'run/user':{'mode':stat.S_IFDIR|0o700,'uid':0,'gid':0,'mtime_ns':1795016822210932469,'xattrs':{}},
    'run/user/0':{'mode':stat.S_IFDIR|0o700,'uid':0,'gid':0,'mtime_ns':1795016822211932463,'xattrs':{}},
    'run/user/0/dconf':{'mode':stat.S_IFDIR|0o700,'uid':0,'gid':0,'mtime_ns':1795016822211932463,'xattrs':{}},
    'run/user/0/dconf/user':{'mode':stat.S_IFREG|0o600,'uid':0,'gid':0,'mtime_ns':1795016822216932437,
        'xattrs':{},'size':2,'sha256':'96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7'}}


def observer_stage8_manifest(image,original):
    """Require the complete original image plus the four exact observer paths."""
    entries={name:{**row,'xattrs':{key:hashlib.sha256(base64.b64decode(value,validate=True)).hexdigest()
        for key,value in row['xattrs'].items()}} for name,row in image['entries'].items()}
    for row in entries.values():
        if 'symlink' in row:row['symlink']=Path(row['symlink']).as_posix()
    expected=original['entries']
    if (set(entries)-set(expected)!=set(STAGE8_DCONF_STATE) or set(expected)-set(entries) or
            any(entries[name]!=row for name,row in STAGE8_DCONF_STATE.items()) or
            expected.get('run',{}).get('mtime_ns')!=1795016359413183630 or
            entries.get('run')!={**expected.get('run',{}),'mtime_ns':1795016822210932469} or
            image['hardlink_groups']!=original['hardlink_groups']):
        raise ValueError('candidate_root_custody_exact_stage8_observer_drift')
    retained={name:row for name,row in entries.items() if name not in STAGE8_DCONF_STATE}
    retained['run']=expected['run']
    if retained!=expected:raise ValueError('candidate_root_custody_stage8_original_full_image_differs')


def observer_stage8_eligible():
    """Archive one frozen post-live root; no cache cleanup or media acceptance."""
    p=payload_module();work=private(WORK,0o700);root=private(ARTIFACT,0o755)
    pin=[root.st_dev,work.st_ino,root.st_ino]
    if pin!=STAGE8_PIN:raise ValueError('candidate_root_custody_stage8_frozen_root_identity')
    preserved={}
    for name,expected in STAGE8_FROZEN.items():
        path=secured(WORK/name)
        if archive.sha(path)!=expected:raise ValueError('candidate_root_custody_stage8_frozen_receipt_changed')
        preserved[str(path)]=expected
    finalized=read(WORK/'finalized.json');live=read(WORK/'live-profile-receipt.json');journal=read(WORK/'evidence/assembly.json')
    if (finalized.get('state')!='native-finalizer-verified' or finalized.get('root')!=VIRTUAL or finalized.get('assembly_pin')!=pin or
            set(finalized.get('checks',{}))!=set(p.CHECKS) or
            any(row.get('passed') is not True or type(row.get('exit_status')) is not int or row['exit_status']!=0 for row in finalized['checks'].values()) or
            live.get('state')!='source-attributed-live-profile-candidate' or live.get('root')!=VIRTUAL or live.get('assembly_pin')!=pin or
            live.get('source_sha256')!=STAGE8_LIVE_SOURCE or live.get('base_image_manifest_sha256')!=finalized.get('image_manifest_sha256') or
            live.get('production_ready') is not False or live.get('native_boot_verified') is not False or live.get('native_login_verified') is not False or
            journal.get('assembled') is not True or journal.get('release_profile') is not True or journal.get('release_accepted') is not False or
            journal.get('g2_eligible') is not False or journal.get('installer_ready') is not False or journal.get('native_image')!=VIRTUAL or
            journal.get('image')!=str(ARTIFACT) or journal.get('live_profile_receipt_sha256')!=STAGE8_FROZEN['live-profile-receipt.json'] or
            journal.get('native_finalizer_receipt_sha256')!=STAGE8_FROZEN['finalized.json']):
        raise ValueError('candidate_root_custody_stage8_actual_live_boundary')
    # The cold boot removed ephemeral /run reports. Their real completed receipt
    # is pinned above; archive eligibility does not rerun or recreate any report.
    source=WORK.parent/'toddy-mvp-live-image-8';source_info=private(source,0o700)
    if source_info.st_ino!=10943708 or source_info.st_dev!=root.st_dev:raise ValueError('candidate_root_custody_stage8_source_identity')
    for name,expected in STAGE8_SOURCE_JOURNALS.items():
        path=secured(source/name)
        if archive.sha(path)!=expected:raise ValueError('candidate_root_custody_stage8_source_journal_changed')
        preserved[str(path)]=expected
    failure=secured(LOG/'b06-generation8-compress.log')
    if archive.sha(failure)!=STAGE8_FAILURE_SHA:
        raise ValueError('candidate_root_custody_stage8_compression_failure_changed')
    preserved[str(failure)]=archive.sha(failure)
    for name in ('toddy-mvp-live-compression-1','toddy-mvp-live-initramfs-1','toddy-mvp-release-media-1'):
        if os.path.lexists(WORK.parent/name):raise ValueError('candidate_root_custody_stage8_unexpected_media_output')
    original=read(WORK/'evidence/image-manifest.json');image=archive.snapshot(ARTIFACT)
    if (len(original['entries']),len(image['entries']))!=STAGE8_ENTRY_COUNTS:raise ValueError('candidate_root_custody_stage8_frozen_entry_count')
    observer_stage8_manifest(image,original)
    inputs=object.__new__(ReviewedInputs);inputs.kind='mvp-live';inputs.base=INPUTS;inputs.bundle=INPUTS/'payload';inputs.recheck()
    if (inputs.descriptor['payload_manifest_sha256']!=finalized.get('payload_manifest_sha256') or
            inputs.descriptor['policy_sha256']!=finalized.get('policy_sha256') or
            inputs.descriptor['image_manifest_sha256']!=finalized.get('image_manifest_sha256') or
            inputs.pins['generated-entries.json']!=finalized.get('generated_entries_sha256')):
        raise ValueError('candidate_root_custody_stage8_signed_inputs_changed')
    paths=[path for path in INPUTS.rglob('*') if path.is_file()]
    paths.extend(ROOT/'scripts/build/phase2'/name for name in ('image_native.sh','candidate_root_custody.py','candidate_root_archive.py'))
    preserved.update({str(path):archive.sha(secured(path)) for path in paths})
    inputs.recheck();no_mounts()
    return {'profile':PROFILE,'assembly_pin':pin,'preserved':preserved,'reviewed_input_pins':inputs.pins,
        'frozen_live_source_sha256':STAGE8_LIVE_SOURCE,'original_image_manifest_sha256':STAGE8_FROZEN['evidence/image-manifest.json'],
        'workflow_boundary':'observed-stage8-root-archival-only-no-media-or-boot-acceptance',
        'exact_observer_paths':sorted(STAGE8_DCONF_STATE),'original_run_mtime_ns':1795016359413183630,
        'observed_run_mtime_ns':1795016822210932469,'root_retirement_only_after_complete_private_host_proof':True,
        'ephemeral_finalizer_reports_replayed':False,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def tar_custody():
    row=subprocess.check_output(['/usr/sbin/chroot',str(TARGET),'/usr/bin/dpkg-query','-W','-f=${Version}\t${Architecture}\t${Status}','tar'],text=True).split('\t')
    if len(row)!=3 or row[2]!='install ok installed':raise ValueError('candidate_root_custody_native_tar_status')
    record=read(Path('/var/log/toddy/packages')/('tar_'+row[0]+'_'+row[1]+'.json'))
    executable=TARGET/'usr/bin/tar'
    if not record.get('installed') or record.get('payload',{}).get('/usr/bin/tar',{}).get('sha256')!=archive.sha(secured(executable)):raise ValueError('candidate_root_custody_native_tar_bytes')
    version=subprocess.check_output(['/usr/sbin/chroot',str(TARGET),'/usr/bin/tar','--version'],text=True).splitlines()[0]
    if version!='tar (GNU tar) 1.35':raise ValueError('candidate_root_custody_native_tar_version')
    return {'version':version,'sha256':archive.sha(executable),'own_archive_sha256':record['archive_sha256'],'record_sha256':archive.sha(Path('/var/log/toddy/packages')/('tar_'+row[0]+'_'+row[1]+'.json'))}


def inspect():
    provenance=eligible();image=archive.snapshot(ARTIFACT);no_consumers(image)
    return {'state':'eligible-'+PROFILE+'-candidate1-custody','provenance':provenance,'entries':len(image['entries']),
        'allocated_regular_bytes':image['allocated_regular_bytes'],'unique_regular_bytes':image['unique_regular_bytes'],'tar_upper_bound_bytes':image['tar_upper_bound_bytes']}


def export():
    if os.path.lexists(CUSTODY):raise ValueError('candidate_root_custody_existing_or_uncertain_no_replay')
    provenance=eligible();image=archive.snapshot(ARTIFACT);no_consumers(image);tool=tar_custody();data=archive.encoded(image)
    payload_module().require_capacity(WORK,len(data)+128*1024**2)
    CUSTODY.mkdir(mode=0o700);fsync(WORK)
    save(CUSTODY/'source-metadata.json',image)
    listing=b'\0'.join(os.fsencode(name) for name in image['entries'])+b'\0'
    with (CUSTODY/'paths.nul').open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(listing);stream.flush();os.fsync(stream.fileno())
    state={'version':1,'state':'export-intended-no-replay','profile':PROFILE,'scope':'One fixed '+PROFILE+' candidate1 expanded root only',
        'provenance':provenance,'metadata_sha256':archive.sha(CUSTODY/'source-metadata.json'),'native_tar':tool,
        'producer_sha256':archive.sha(Path(__file__)),'archive_verifier_sha256':archive.sha(Path(archive.__file__)),
        'root':str(ARTIFACT),'entries':len(image['entries']),'allocated_regular_bytes':image['allocated_regular_bytes'],
        'tar_upper_bound_bytes':image['tar_upper_bound_bytes']}
    save(STATE,state)
    command=['/usr/sbin/chroot',str(TARGET),'/usr/bin/tar','--create','--file=-','--format=pax',
        '--pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime','--acls','--xattrs','--xattrs-include=*',
        '--numeric-owner','--sparse','--no-recursion','--null','--verbatim-files-from','--directory='+VIRTUAL,
        '--files-from=/'+str((CUSTODY/'paths.nul').relative_to(TARGET))]
    count=0;digest=hashlib.sha256()
    with (CUSTODY/'create.log').open('xb') as log:
        os.fchmod(log.fileno(),0o600);process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=log)
        try:
            while chunk:=process.stdout.read(archive.CHUNK):
                count+=len(chunk)
                if count>image['tar_upper_bound_bytes']:raise ValueError('candidate_root_custody_tar_bound')
                digest.update(chunk);sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
            if process.wait(timeout=60):raise ValueError('candidate_root_custody_tar_failed')
        finally:
            process.stdout.close()
            if process.poll() is None:process.terminate();process.wait(timeout=10)
            log.flush();os.fsync(log.fileno())
    if eligible()!=provenance or archive.snapshot(ARTIFACT)!=image:raise ValueError('candidate_root_custody_source_changed_during_export')
    state.update(state='exported-awaiting-host-proof',tar_bytes=count,tar_sha256=digest.hexdigest());save(STATE,state)


def retire(proof):
    state=read(STATE)
    required={'version','state','metadata_sha256','tar_sha256','tar_bytes','compressed_sha256','compressed_bytes','host_receipt_sha256','member_proof'}
    if (not isinstance(proof,dict) or set(proof)!=required or proof['version']!=1 or proof['state']!='complete-member-and-decompression-verified' or
            state.get('state')!='exported-awaiting-host-proof' or state.get('profile')!=PROFILE or state.get('root')!=str(ARTIFACT) or
            state.get('producer_sha256')!=archive.sha(Path(__file__)) or state.get('archive_verifier_sha256')!=archive.sha(Path(archive.__file__)) or
            proof['metadata_sha256']!=state['metadata_sha256'] or
            proof['tar_sha256']!=state['tar_sha256'] or proof['tar_bytes']!=state['tar_bytes'] or
            any(not isinstance(proof[key],str) or not __import__('re').fullmatch('[a-f0-9]{64}',proof[key]) for key in ('compressed_sha256','host_receipt_sha256')) or
            type(proof['compressed_bytes']) is not int or proof['compressed_bytes']<=0):raise ValueError('candidate_root_custody_durable_host_proof_required')
    image=read(CUSTODY/'source-metadata.json')
    if archive.sha(CUSTODY/'source-metadata.json')!=state['metadata_sha256'] or eligible()!=state['provenance'] or archive.snapshot(ARTIFACT)!=image:raise ValueError('candidate_root_custody_source_changed_before_retire')
    expected={'state':'all-members-bytes-metadata-verified','entries':len(image['entries']),'unique_regular_bytes':image['unique_regular_bytes'],
        'xattrs_ACLs_symlinks_hardlink_classes_verified':True,'privileged_extraction_performed':False}
    if proof['member_proof']!=expected:raise ValueError('candidate_root_custody_complete_metadata_proof_required')
    if not shutil.rmtree.avoids_symlink_attacks:raise ValueError('candidate_root_custody_fd_safe_removal_required')
    no_consumers(image);before=shutil.disk_usage(TARGET).free
    state.update(state='root-retirement-intended-no-replay',host_proof=proof,before_free_bytes=before);save(STATE,state)
    # No arbitrary path, candidate parent, accepted root, bundle or journal enters
    # this deletion. Root-owned parent+inode pins were rechecked above.
    shutil.rmtree(ARTIFACT);fsync(WORK)
    for path,sha in state['provenance']['preserved'].items():
        if archive.sha(secured(path,8*1024**3 if PROFILE in HISTORICAL else 256*1024**2))!=sha:raise ValueError('candidate_root_custody_preserved_evidence_changed')
    for path,expected in state['provenance'].get('preserved_links',{}).items():
        if preserved_link(Path(path),Path(expected['tree']))!=expected:raise ValueError('candidate_root_custody_preserved_link_changed')
    if os.path.lexists(ARTIFACT):raise ValueError('candidate_root_custody_root_remains')
    state.update(state='complete',after_free_bytes=shutil.disk_usage(TARGET).free,root_removed=True,
        recovery='Restore retained private tar into NEW guarded native candidate directory; compare full metadata and hardlink classes. Never replay old unpack/resource generation.')
    state['actual_guest_free_gain_bytes']=state['after_free_bytes']-before;save(STATE,state);return state



def validate_lease(fd):
    path=secured(LOCK);actual=os.fstat(fd);expected=path.stat()
    if LOCK.resolve()!=LOCK or Path('/proc/self/fd/'+str(fd)).readlink()!=LOCK or (actual.st_dev,actual.st_ino)!=(expected.st_dev,expected.st_ino):
        raise ValueError('candidate_root_custody_global_lease_identity')
    info=Path('/proc/self/fdinfo/'+str(fd)).read_text()
    if not re.search(r'^lock:.*\bFLOCK\b.*\bWRITE\b',info,re.M):raise ValueError('candidate_root_custody_exclusive_global_lease_required')


@contextmanager
def operation_lease():
    try:os.fstat(9)
    except OSError as error:
        if error.errno!=errno.EBADF:raise
        fd=os.open(LOCK,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);validate_lease(fd);yield fd
        finally:os.close(fd)
    else:
        # image_native owns this same open description. Never open/reacquire or
        # unlock/close its FD9; it remains held across helper and namespace cleanup.
        validate_lease(9);yield 9


def main():
    arguments=sys.argv[1:]
    if arguments and arguments[0] in ('live','mvp-offline','mvp-live','mvp-live-failed1','mvp-live-failed3','mvp-live-failed4','mvp-live-failed5','mvp-live-stage6','mvp-live-stage7','mvp-live-stage8','h10-expanded','h11-expanded'):configure(arguments[0]);arguments=arguments[1:]
    if os.getuid()!=0 or os.geteuid()!=0 or arguments not in (['inspect'],['export'],['receipt'],['metadata'],['retire']):raise ValueError('candidate_root_custody_fixed_root_coordinator_action')
    os.umask(0o077);subprocess.run(['/bin/bash','-c','source "$1"; guard_target','guard',str(ROOT/'scripts/build/target.sh')],check=True)
    with operation_lease():
        if list(LOCK.parent.glob('*.running.json')) or (LOCK.parent/'input-sync.running').exists() or unclosed_compiler_jobs(LOG):raise ValueError('candidate_root_custody_other_native_operation')
        action=arguments[0]
        if action=='export':export();return
        if action=='inspect':result=inspect()
        elif action=='receipt':result=read(STATE)
        elif action=='metadata':result=read(CUSTODY/'source-metadata.json')
        else:
            data=sys.stdin.buffer.read(65537)
            if len(data)>65536:raise ValueError('candidate_root_custody_proof_size')
            result=retire(payload_module().strict(data))
        sys.stdout.buffer.write(archive.encoded(result));sys.stdout.buffer.flush()

if __name__=='__main__':main()
