#!/usr/bin/env python3
"""Private opaque custody for fixed expanded roots; never host extraction.

Root guest retirement is requested only after independent full member/PAX/ACL/
hardlink/byte and complete gzip decompression proof, with durable host custody.
"""
import fcntl,gzip,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
import phase2_candidate_vm as candidate
from mvp_delivery_storage import host_floor
import vm
ROOT=vm.ROOT

def configure(profile):
    global PROFILE,CONTEXT,ARCHIVE_NAME
    if profile not in ('offline','live','mvp-offline','mvp-live','mvp-live-failed1','mvp-live-failed3','mvp-live-failed4','mvp-live-failed5','mvp-live-stage6','mvp-live-stage7','mvp-live-stage8','h10-expanded','h11-expanded'):raise ValueError('candidate_root_host_unknown_fixed_profile')
    generation=9 if profile=='mvp-live' else 8 if profile=='mvp-live-stage8' else 7 if profile=='mvp-live-stage7' else 6 if profile=='mvp-live-stage6' else 5 if profile=='mvp-live-failed5' else 4 if profile=='mvp-live-failed4' else 3 if profile=='mvp-live-failed3' else 1
    PROFILE=profile;CONTEXT=ROOT/'.local/phase2'/(profile+f'-candidate-root-custody-{generation}');ARCHIVE_NAME=profile+f'-candidate{generation}-root.tar.gz'
    if profile in ('h10-expanded','h11-expanded'):
        CONTEXT=ROOT/'.local/phase2'/(profile+'-root-custody-1');ARCHIVE_NAME=profile+'-root.tar.gz'

configure('offline')
sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import candidate_root_archive as archive
GUEST='/opt/toddy-build/scripts/build/phase2/image_native.sh'
CHUNK=4*1024**2


def fsync(path):
    fd=os.open(path,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def save(path,value):
    part=path.with_suffix('.part')
    with part.open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(archive.encoded(value));stream.flush();os.fsync(stream.fileno())
    os.replace(part,path);fsync(path.parent)

def command(action):
    if action not in ('inspect','export','receipt','metadata','retire'):raise ValueError('candidate_root_host_fixed_action')
    ssh=candidate.ssh()
    return [*ssh[:-1],'-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',ssh[-1],'/usr/bin/bash '+GUEST+' custody-'+PROFILE+'-'+action]

def read_guest(action,limit=128*1024**2):
    result=subprocess.run(command(action),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=1800)
    if len(result.stdout)>limit:raise ValueError('candidate_root_host_receipt_bound')
    return json.loads(result.stdout)

def same_guest(identity):
    if candidate.owned()!=identity:raise ValueError('candidate_root_host_guest_changed')
    candidate.bases()


def stream_compress(source,destination,upper):
    count=0;digest=hashlib.sha256()
    with destination.open('xb') as output:
        os.fchmod(output.fileno(),0o600)
        with gzip.GzipFile(filename='',mode='wb',fileobj=output,compresslevel=1,mtime=0) as compressed:
            while chunk:=source.read(CHUNK):
                count+=len(chunk)
                if count>upper:raise ValueError('candidate_root_host_tar_admission_bound')
                digest.update(chunk);compressed.write(chunk)
        output.flush();os.fsync(output.fileno())
    if count==0:raise ValueError('candidate_root_host_empty_export')
    return {'tar_sha256':digest.hexdigest(),'tar_bytes':count}


class Counted:
    def __init__(self,stream,limit):self.stream=stream;self.limit=limit;self.count=0;self.digest=hashlib.sha256()
    def read(self,size=-1):
        if size<0:raise ValueError('candidate_root_host_unbounded_decompression_read')
        data=self.stream.read(size);self.count+=len(data)
        if self.count>self.limit:raise ValueError('candidate_root_host_decompression_bound')
        self.digest.update(data);return data


def verify_compressed(path,metadata,expected):
    info=path.lstat()
    if path.resolve()!=path or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:raise ValueError('candidate_root_host_private_archive')
    before=(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns)
    with gzip.open(path,'rb') as stream:
        counted=Counted(stream,expected['tar_bytes']);proof=archive.verify_tar(counted,metadata)
        while counted.read(CHUNK):pass
        if counted.count!=expected['tar_bytes'] or counted.digest.hexdigest()!=expected['tar_sha256']:raise ValueError('candidate_root_host_complete_decompression_differs')
    if before!=(path.stat().st_dev,path.stat().st_ino,path.stat().st_size,path.stat().st_mtime_ns):raise ValueError('candidate_root_host_archive_changed_during_proof')
    return {'version':1,'state':'complete-member-and-decompression-verified','metadata_sha256':hashlib.sha256(archive.encoded(metadata)).hexdigest(),
        **expected,'compressed_sha256':archive.sha(path),'compressed_bytes':info.st_size,'member_proof':proof}


def main(profile='offline'):
    configure(profile)
    if sys.argv[1:] or os.geteuid()==0 or ROOT.resolve()!=ROOT:raise ValueError('candidate_root_host_fixed_unprivileged_command')
    os.umask(0o077);parent=CONTEXT.parent
    if parent.resolve()!=parent or not parent.is_dir() or parent.stat().st_uid!=os.getuid():raise ValueError('candidate_root_host_private_parent')
    with (vm.VM/'native-boot-test.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if os.path.lexists(CONTEXT):raise ValueError('candidate_root_host_existing_or_uncertain_no_replay')
        identity=candidate.owned();candidate.bases();selected=read_guest('inspect')
        if selected.get('state')!='eligible-'+PROFILE+'-candidate1-custody' or type(selected.get('tar_upper_bound_bytes')) is not int or selected['tar_upper_bound_bytes']<=0:raise ValueError('candidate_root_host_actual_eligibility_required')
        reserve=(host_floor(True) if PROFILE in ('mvp-live-failed1','mvp-live-failed3','mvp-live-failed4','mvp-live-failed5','mvp-live-stage6','mvp-live-stage7','mvp-live-stage8') else
            json.loads((ROOT/'config/build-host.lock.json').read_bytes())['host_free_reserve_gib']*1024**3)
        upper=selected['tar_upper_bound_bytes'];space=os.statvfs(parent)
        if space.f_bavail*space.f_frsize<reserve+upper+512*1024**2:raise ValueError('candidate_root_host_reserve_plus_whole_stream_bound')
        CONTEXT.mkdir(mode=0o700);fsync(parent)
        state={'version':1,'state':'export-intended-no-replay','candidate_container_id':identity,'actual_selection':selected,
            'guest_helper_sha256':archive.sha(ROOT/'scripts/build/phase2/candidate_root_custody.py'),
            'protected_view_driver_sha256':archive.sha(ROOT/'scripts/build/phase2/image_native.sh'),
            'archive_verifier_sha256':archive.sha(Path(archive.__file__)),'host_producer_sha256':archive.sha(Path(__file__)),
            'profile':PROFILE,'host_entry_sha256':archive.sha(Path(sys.argv[0]).resolve()),
            'scope':('Only frozen stage8 observer-drift root; all journals/signed bundles/other roots/accepted backings retained' if PROFILE=='mvp-live-stage8' else
                     'Only fixed '+PROFILE+' candidate1 root; all journals/final roots/signed bundles/accepted backings retained')}
        save(CONTEXT/'result.json',state);partial=CONTEXT/(ARCHIVE_NAME+'.part');packed=CONTEXT/ARCHIVE_NAME
        with (CONTEXT/'export.log').open('xb') as log:
            os.fchmod(log.fileno(),0o600);process=subprocess.Popen(command('export'),stdout=subprocess.PIPE,stderr=log)
            try:
                expected=stream_compress(process.stdout,partial,upper)
                if process.wait(timeout=60):raise ValueError('candidate_root_host_export_failed')
            finally:
                process.stdout.close()
                if process.poll() is None:process.terminate();process.wait(timeout=30)
                log.flush();os.fsync(log.fileno())
        os.rename(partial,packed);fsync(CONTEXT);same_guest(identity)
        guest=read_guest('receipt');metadata=read_guest('metadata')
        if (guest.get('state')!='exported-awaiting-host-proof' or guest.get('profile')!=PROFILE or guest.get('producer_sha256')!=state['guest_helper_sha256'] or
                guest.get('archive_verifier_sha256')!=state['archive_verifier_sha256'] or guest.get('provenance',{}).get('preserved',{}).get(GUEST)!=state['protected_view_driver_sha256'] or guest.get('provenance')!=selected['provenance'] or
                any(guest.get(key)!=value for key,value in expected.items()) or guest.get('metadata_sha256')!=hashlib.sha256(archive.encoded(metadata)).hexdigest()):raise ValueError('candidate_root_host_export_binding_differs')
        save(CONTEXT/'guest-export.json',guest);save(CONTEXT/'source-metadata.json',metadata)
        proof=verify_compressed(packed,metadata,expected)
        state.update(state='complete-member-and-decompression-verified',host_archive=str(packed),host_proof=proof,
            guest_export_sha256=archive.sha(CONTEXT/'guest-export.json'),privileged_extraction_performed=False,root_payload_executed=False)
        save(CONTEXT/'result.json',state);save(CONTEXT/'host-verified.json',state)
        proof['host_receipt_sha256']=archive.sha(CONTEXT/'host-verified.json')
        if archive.sha(packed)!=proof['compressed_sha256']:raise ValueError('candidate_root_host_archive_changed_before_retire')
        same_guest(identity)
        result=subprocess.run(command('retire'),input=archive.encoded(proof),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=1800)
        if len(result.stdout)>128*1024**2:raise ValueError('candidate_root_host_retirement_receipt_bound')
        retired=json.loads(result.stdout)
        if retired.get('state')!='complete' or retired.get('host_proof')!=proof or retired.get('root_removed') is not True:raise ValueError('candidate_root_host_retirement_not_complete')
        same_guest(identity);save(CONTEXT/'guest-retired.json',retired)
        state.update(state='complete',retirement_receipt_sha256=archive.sha(CONTEXT/'guest-retired.json'),
            actual_guest_free_gain_bytes=retired['actual_guest_free_gain_bytes'],host_trim_claimed=False)
        save(CONTEXT/'result.json',state);print(archive.encoded({'state':'complete','context':str(CONTEXT),
            'actual_guest_free_gain_bytes':retired['actual_guest_free_gain_bytes'],'host_trim_claimed':False}).decode(),end='')

if __name__=='__main__':main()
