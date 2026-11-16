#!/usr/bin/env python3
"""Fixed candidate and historical root custody profiles; no arbitrary paths.

Offline after real matching finalizer2; live before fresh finalizer2 only from
completed resource candidate and exact independently reviewed protected inputs.
No generic path/cleanup flag.
"""
import base64,errno,fcntl,hashlib,json,os,re,shutil,stat,subprocess,sys
from contextlib import contextmanager
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path('/opt/toddy-build');TARGET=Path('/mnt/lfs')
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parents[3])]
import candidate_root_archive as archive
from runtime.installer.composition import secured,validate_finalizer_report
from runtime.installer.native_finalizer import payload_module
from image_assemble import unclosed_compiler_jobs,ReviewedInputs
PROFILES={'offline':('toddy-offline-image-1','toddy-offline-image-2','offline-root-2','toddy-installer-native-inputs'),
          'live':('toddy-live-image-1','toddy-live-image-2','live-root-2','toddy-live-native-inputs'),
          'mvp-offline':('toddy-mvp-offline-image-1','toddy-mvp-offline-image-2','mvp-offline-root-2','toddy-mvp-installer-native-inputs'),
          'mvp-live':('toddy-mvp-live-image-1','toddy-mvp-live-image-2','mvp-live-root-2','toddy-mvp-live-native-inputs')}


HISTORICAL={'h10-expanded':('h10-live-root',8707435,1794055093154113811,'h10'),
            'h11-expanded':('h11-release-root',1239394,1794056902695122701,'h11')}


def configure(profile):
    global PROFILE,WORK,ARTIFACT,REVIEWED,FINAL_ROOT,INPUTS,CUSTODY,STATE,VIRTUAL
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
    if arguments and arguments[0] in ('live','mvp-offline','mvp-live','h10-expanded','h11-expanded'):configure(arguments[0]);arguments=arguments[1:]
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
