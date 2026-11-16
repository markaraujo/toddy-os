"""One-shot online growth of the exact disposable candidate target, never host disks."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import candidate_target_geometry as geometry
import run_step

BASE=Path('/var/log/toddy/phase2/candidate-target-growth-1')
QUALIFIED=BASE.with_name('candidate-target-growth-qualified-1.json')
MARKER=Path('/var/log/toddy/build/candidate-target-growth-1.running.json')
TOOLS=('sfdisk','partx','resize2fs','dumpe2fs','blockdev','blkid','findmnt','lsblk')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def command(*args):return subprocess.check_output(args,text=True,stderr=subprocess.PIPE).strip()
def save(name,value):run_step.write(BASE/(name+'.json'),value)


def source_pins():return {name:digest(HERE/name) for name in ('grow_candidate_target.py','candidate_target_geometry.py')}


def tool_pins():
    result={}
    for name in TOOLS:
        path=Path(shutil.which(name) or '')
        if not path.is_absolute() or not path.is_file():raise ValueError('Required native growth tool missing: '+name)
        result[name]={'path':str(path),'sha256':digest(path)}
    return result


def identity():
    if os.getuid()!=0 or os.geteuid()!=0 or socket.gethostname()!='toddy-builder' or command('systemd-detect-virt') not in ('kvm','qemu'):raise ValueError('Dedicated virtual builder root required')
    if command('lsblk','-dn','-o','SERIAL','/dev/vdb')!=geometry.SERIAL or command('lsblk','-dn','-o','SERIAL','/dev/vda')!='TODDY-BUILDER' or command('findmnt','-n','-o','SOURCE','/')!='/dev/vda1':raise ValueError('Exact virtual target/builder identity required')
    target=Path('/mnt/lfs')
    if target.resolve()!=target or not target.is_dir() or stat.S_IMODE(target.stat().st_mode)!=0o755:raise ValueError('Canonical target mount required')
    mount=json.loads(command('findmnt','--json','--output','TARGET,SOURCE,FSTYPE,OPTIONS','--mountpoint',str(target)))['filesystems']
    if len(mount)!=1 or mount[0]['target']!='/mnt/lfs' or mount[0]['source']!='/dev/vdb4' or mount[0]['fstype']!='ext4' or 'rw' not in mount[0]['options'].split(','):raise ValueError('Exact mounted ext4 target required')
    if command('blkid','-s','UUID','-o','value','/dev/vdb4')!=geometry.UUID or command('blkid','-s','PARTUUID','-o','value','/dev/vdb4').lower()!=geometry.ROOT_PARTUUID or command('blkid','-s','LABEL','-o','value','/dev/vdb4')!='TODDY_LFS' or command('lsblk','-dn','-o','PKNAME','/dev/vdb4')!='vdb':raise ValueError('Exact target filesystem/partition identity required')
    node=Path('/dev/vdb').stat()
    if not stat.S_ISBLK(node.st_mode):raise ValueError('Verified virtual block target required')
    return {'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'serial':geometry.SERIAL,'filesystem_uuid':geometry.UUID,'partuuid':geometry.ROOT_PARTUUID,'disk_bytes':int(command('blockdev','--getsize64','/dev/vdb')),'kernel_partition_bytes':int(command('blockdev','--getsize64','/dev/vdb4')),'mount':mount[0],'device_rdev':node.st_rdev}


def disk_table():return json.loads(command('sfdisk','--json','/dev/vdb'))['partitiontable']


def filesystem():
    fields={line.partition(':')[0].strip():line.partition(':')[2].strip() for line in command('dumpe2fs','-h','/dev/vdb4').splitlines() if ':' in line}
    if fields['Filesystem UUID']!=geometry.UUID or int(fields['Block size'])!=4096:raise ValueError('Expected ext4 UUID/block size required')
    return {'uuid':fields['Filesystem UUID'],'block_size':int(fields['Block size']),'block_count':int(fields['Block count'])}


def gpt(size,backup=False):
    fd=os.open('/dev/vdb',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        result=geometry.gpt(lambda count,offset:os.pread(fd,count,offset),size)
        if backup:
            for name,count,offset in (('first34-sectors',34*512,0),('last33-sectors',33*512,size-33*512)):
                with (BASE/(name+'.bin')).open('xb') as stream:os.fchmod(stream.fileno(),0o600);stream.write(os.pread(fd,count,offset));stream.flush();os.fsync(stream.fileno())
        return result
    finally:os.close(fd)


def checked_completed():
    # This small public root-owned receipt is readable by ordinary build guards;
    # complete private raw GPT/snapshot/exit evidence remains separately retained.
    for path in (QUALIFIED,*QUALIFIED.parents):
        info=path.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('Root-owned qualified growth receipt required')
    if not stat.S_ISREG(QUALIFIED.stat().st_mode) or QUALIFIED.stat().st_size>65536:raise ValueError('Bounded growth receipt required')
    value=json.loads(QUALIFIED.read_bytes())
    if value.get('state')!='filesystem-grown-and-full-root-unchanged' or value.get('old_bytes')!=geometry.OLD or value.get('new_bytes')!=geometry.NEW or value.get('producer_pins')!=source_pins() or value.get('full_root_changed_paths')!=0 or MARKER.exists():raise ValueError('Exact completed growth receipt required')
    actual=identity();geometry.verify_table(disk_table(),geometry.NEW);fs=filesystem()
    if actual['disk_bytes']!=geometry.NEW or actual['kernel_partition_bytes']!=geometry.partition_bytes(geometry.NEW) or fs['block_count']*fs['block_size']!=geometry.partition_bytes(geometry.NEW) or value.get('gpt')!=gpt(geometry.NEW):raise ValueError('Completed disk/kernel/GPT/ext4 geometry differs')
    return value


def finish_growth(before,pins,tools):
    # Virtio resize notification is asynchronous. Poll only its read-only size;
    # never retry QMP or admit GPT writes against the old kernel capacity.
    for attempt in range(120):
        size=int(command('blockdev','--getsize64','/dev/vdb'))
        if size==geometry.NEW:break
        if size!=geometry.OLD:raise ValueError('Unexpected kernel disk capacity')
        time.sleep(.25)
    else:raise ValueError('Kernel did not observe QMP/cold disk growth')
    now=identity()
    if now['disk_bytes']!=geometry.NEW or any(now[key]!=before[key] for key in ('boot_id','serial','filesystem_uuid','partuuid','mount','device_rdev')) or now['kernel_partition_bytes']!=before['kernel_partition_bytes'] or source_pins()!=pins or tool_pins()!=tools:raise ValueError('Identity changed before GPT update')
    geometry.verify_table(disk_table(),geometry.OLD)
    plan=geometry.script();(BASE/'partition-table.planned.txt').write_text(plan)
    def execute(name,args,input=None):
        save(name+'-intent',{'command':args,'input_sha256':None if input is None else hashlib.sha256(input.encode()).hexdigest()})
        with (BASE/(name+'.log')).open('xb') as output:
            result=subprocess.run(args,input=None if input is None else input.encode(),stdout=output,stderr=subprocess.STDOUT)
        save(name+'-exit',{'exit':result.returncode})
        if result.returncode:raise ValueError('Growth step failed; inspect actual postcondition: '+name)
    common=['sfdisk','--lock=yes','--no-reread','--no-tell-kernel','--wipe=never','--wipe-partitions=never']
    execute('gpt-dry-run',common+['--no-act','/dev/vdb'],plan)
    execute('gpt-write',common+['/dev/vdb'],plan)
    geometry.verify_table(disk_table(),geometry.NEW);after_gpt=gpt(geometry.NEW);save('gpt-after',after_gpt)
    fd=os.open('/dev/vdb',os.O_RDONLY|os.O_NOFOLLOW)
    try:
        if os.pread(fd,440,0)!=(BASE/'first34-sectors.bin').read_bytes()[:440]:raise ValueError('Existing BIOS MBR boot code changed')
    finally:os.close(fd)
    execute('kernel-partition-update',['partx','--update','--nr','4','/dev/vdb'])
    if int(command('blockdev','--getsize64','/dev/vdb4'))!=geometry.partition_bytes(geometry.NEW):raise ValueError('Kernel partition not grown; ext4 step not admitted')
    execute('ext4-grow',['resize2fs','/dev/vdb4'])
    final=identity();geometry.verify_table(disk_table(),geometry.NEW);after_fs=filesystem()
    if final['disk_bytes']!=geometry.NEW or final['kernel_partition_bytes']!=geometry.partition_bytes(geometry.NEW) or after_fs['block_count']*after_fs['block_size']!=geometry.partition_bytes(geometry.NEW) or gpt(geometry.NEW)!=after_gpt:raise ValueError('Final disk/kernel/GPT/ext4 geometry differs')
    after=run_step.snapshot();save('full-root-after',after)
    original=json.loads((BASE/'full-root-before.json').read_bytes());changes={name:{'before':original.get(name),'after':after.get(name)} for name in original.keys()|after.keys() if original.get(name)!=after.get(name)}
    save('full-root-manifest',changes)
    if changes:raise ValueError('Unexpected existing full-root file mutation')
    value={'state':'filesystem-grown-and-full-root-unchanged','old_bytes':geometry.OLD,'new_bytes':geometry.NEW,'identity':final,'filesystem':after_fs,'gpt':after_gpt,'producer_pins':pins,'intent_sha256':digest(BASE/'intent.json'),'full_root_changed_paths':0,'free_bytes':os.statvfs('/mnt/lfs').f_bavail*os.statvfs('/mnt/lfs').f_frsize}
    save('complete',value);MARKER.unlink()
    with QUALIFIED.open('x') as output:os.fchmod(output.fileno(),0o644);json.dump(value,output,sort_keys=True);output.write('\n');output.flush();os.fsync(output.fileno())
    parent=os.open(QUALIFIED.parent,os.O_DIRECTORY)
    try:os.fsync(parent)
    finally:os.close(parent)
    checked_completed();print(json.dumps({'event':'complete','receipt':value}),flush=True)


def serve(cold=False):
    before=identity()
    if before['disk_bytes']!=geometry.OLD or before['kernel_partition_bytes']!=geometry.partition_bytes(geometry.OLD):raise ValueError('Only exact180GiB candidate can enter this operation')
    geometry.verify_table(disk_table(),geometry.OLD);fs=filesystem()
    if fs['block_count']*fs['block_size']!=geometry.partition_bytes(geometry.OLD):raise ValueError('Original ext4 geometry differs')
    if os.path.lexists(BASE) or os.path.lexists(QUALIFIED) or os.path.lexists(MARKER):raise ValueError('Inspect prior growth state; never replay')
    with Path('/var/log/toddy/build/build.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if list(MARKER.parent.glob('*.running.json')):raise ValueError('Reconcile existing native writer first')
        BASE.mkdir(mode=0o700);pins=source_pins();tools=tool_pins()
        intent={'state':'waiting-for-exact-host-QMP-growth','identity':before,'table':disk_table(),'filesystem':fs,'producer_pins':pins,'tool_pins':tools,'old_bytes':geometry.OLD,'new_bytes':geometry.NEW}
        save('intent',intent);run_step.write(MARKER,{'operation':'candidate-target-growth-1','intent_sha256':digest(BASE/'intent.json'),'boot_id':before['boot_id']})
        try:
            original_gpt=gpt(geometry.OLD,backup=True);save('gpt-before',original_gpt)
            (BASE/'partition-table.before.txt').write_text(command('sfdisk','--dump','/dev/vdb')+'\n')
            save('full-root-before',run_step.snapshot())
            if cold:
                save('cold-prepared',{'intent_sha256':digest(BASE/'intent.json'),'full_root_before_sha256':digest(BASE/'full-root-before.json')})
                print(json.dumps({'event':'cold-prepared','identity':before,'producer_pins':pins,'intent_sha256':digest(BASE/'intent.json')}),flush=True);return
            print(json.dumps({'event':'ready','identity':before,'producer_pins':pins,'intent_sha256':digest(BASE/'intent.json'),'gpt':original_gpt}),flush=True)
            if sys.stdin.readline(16)!='GROW\n':raise ValueError('Host did not confirm exact QMP growth')
            finish_growth(before,pins,tools)
        except BaseException as error:
            save('failed',{'state':'inspect-no-replay','error_type':type(error).__name__,'reason':str(error)[:512]})
            raise


def finish_cold():
    if not BASE.is_dir() or not MARKER.is_file() or not (BASE/'cold-prepared.json').is_file() or any((BASE/name).exists() for name in ('failed.json','complete.json','cold-finish-intent.json')):raise ValueError('Exact previously prepared cold growth required; no replay')
    original=json.loads((BASE/'intent.json').read_bytes());prepared=json.loads((BASE/'cold-prepared.json').read_bytes())
    if prepared['intent_sha256']!=digest(BASE/'intent.json') or prepared['full_root_before_sha256']!=digest(BASE/'full-root-before.json') or original['producer_pins']!=source_pins() or original['tool_pins']!=tool_pins():raise ValueError('Cold growth prepared source/evidence changed')
    with Path('/var/log/toddy/build/build.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if set(MARKER.parent.glob('*.running.json'))!={MARKER}:raise ValueError('Another native writer remains unreconciled')
        now=identity();before=dict(original['identity'])
        if now['boot_id']==before['boot_id'] or now['disk_bytes']!=geometry.NEW:raise ValueError('Cold resized candidate must actually reboot first')
        before['boot_id']=now['boot_id'] # Explicit cold path; old identity remains in immutable intent.
        save('cold-finish-intent',{'boot_id':now['boot_id'],'old_boot_id':original['identity']['boot_id'],'intent_sha256':digest(BASE/'intent.json')})
        try:finish_growth(before,original['producer_pins'],original['tool_pins'])
        except BaseException as error:
            save('failed',{'state':'inspect-no-replay','error_type':type(error).__name__,'reason':str(error)[:512]});raise


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['serve','prepare-cold','finish-cold','inspect','guard']);args=parser.parse_args()
    os.umask(0o022)
    if args.action=='serve':serve()
    elif args.action=='prepare-cold':serve(cold=True)
    elif args.action=='finish-cold':finish_cold()
    elif args.action=='guard':checked_completed()
    else:print(json.dumps({'identity':identity(),'table':disk_table(),'filesystem':filesystem(),'private_evidence_exists':BASE.exists(),'qualified_receipt_exists':QUALIFIED.exists(),'running_marker_exists':MARKER.exists()},sort_keys=True))


if __name__=='__main__':main()
