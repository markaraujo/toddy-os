#!/usr/bin/env python3
"""One-shot custody of already selected Qwen bytes; never download or activate."""
import fcntl,hashlib,json,os,shutil,stat,subprocess,sys
from pathlib import Path
TARGET=Path('/mnt/lfs')
LOG=Path('/var/log/toddy/phase2')
RECEIPT=LOG/'qwen3-1.7b-qualification-custody-1.json'
LOCK=Path('/var/log/toddy/build/build.lock')
ROWS=(('sources/phase2/inputs/local-model-proof/model.gguf','usr/share/toddy/models/qualification-qwen3-1.7b-1/model.gguf',1834426016,'061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a'),
      ('sources/qwen-LICENSE','usr/share/doc/toddy-native-qwen3-1.7b-qualification-1/LICENSE',11544,'5de36594c10839788a8c589443a8ef9d8b8d17c65a1b5807206ae037fc36c6bd'))
ADDITIONAL=sum(row[2] for row in ROWS)
MARGIN=512*1024**2

def reserve(path,floor):
    free=shutil.disk_usage(path).free
    if free<floor+MARGIN+ADDITIONAL:raise ValueError('qwen_custody_reserve')
    return {'free_bytes':free,'floor_bytes':floor,'margin_bytes':MARGIN,'copy_bytes':ADDITIONAL}

def protected(path,directory=True):
    path=Path(path)
    if path.resolve()!=path:raise ValueError('qwen_custody_redirected_output')
    for parent in path.parents:
        info=parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid or info.st_mode&0o022:raise ValueError('qwen_custody_unprotected_ancestor')
    info=path.lstat()
    if info.st_uid or info.st_gid or info.st_mode&0o022 or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1):raise ValueError('qwen_custody_unprotected_output')
    return info

def fingerprint(info,size):
    if not stat.S_ISREG(info.st_mode) or info.st_uid or info.st_gid or info.st_nlink!=1 or info.st_size!=size or stat.S_IMODE(info.st_mode) not in (0o644,0o664):raise ValueError('qwen_custody_legacy_source_identity')
    return [info.st_dev,info.st_ino,info.st_mode,info.st_uid,info.st_gid,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_atime_ns]

def fd_hash(fd):
    os.lseek(fd,0,os.SEEK_SET);digest=hashlib.sha256()
    while chunk:=os.read(fd,1024**2):digest.update(chunk)
    os.lseek(fd,0,os.SEEK_SET)
    return digest.hexdigest()

def sync_dir(path):
    fd=os.open(path,os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)

def save(value):
    part=RECEIPT.with_suffix('.part')
    with part.open('x') as stream:
        os.fchmod(stream.fileno(),0o600);json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(part,RECEIPT);sync_dir(RECEIPT.parent)

def make_parent(path):
    missing=[];current=path
    while not current.exists():missing.append(current);current=current.parent
    protected(current)
    for parent in reversed(missing):parent.mkdir(mode=0o755);sync_dir(parent.parent)
    protected(path)

def copy_one(fd,source,destination,size,expected,before):
    out=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    count=0;digest=hashlib.sha256()
    with os.fdopen(out,'wb') as stream:
        while chunk:=os.read(fd,1024**2):
            count+=len(chunk)
            if count>size:raise ValueError('qwen_custody_source_grew')
            digest.update(chunk);stream.write(chunk)
        stream.flush();os.fsync(stream.fileno());os.fchmod(stream.fileno(),0o444);os.fsync(stream.fileno())
    if count!=size or digest.hexdigest()!=expected or fingerprint(os.fstat(fd),size)!=before or fingerprint(source.lstat(),size)!=before:raise ValueError('qwen_custody_source_changed')
    protected(destination,False)
    check=os.open(destination,os.O_RDONLY|os.O_NOFOLLOW|os.O_NOATIME)
    try:
        if fd_hash(check)!=expected:raise ValueError('qwen_custody_copy_changed')
    finally:os.close(check)
    sync_dir(destination.parent)

def custody():
    if os.geteuid()!=0:raise ValueError('qwen_custody_root_required')
    os.umask(0o022)
    subprocess.run(['/bin/bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    protected(LOG);protected(LOCK,False)
    lease=os.open(LOCK,os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        if os.fstat(lease).st_ino!=LOCK.stat().st_ino or os.fstat(lease).st_dev!=LOCK.stat().st_dev:raise ValueError('qwen_custody_lock_changed')
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if list(LOCK.parent.glob('*.running.json')):raise ValueError('qwen_custody_native_transaction_unresolved')
        if any(os.path.lexists(p) for p in (RECEIPT,RECEIPT.with_suffix('.part'),*(TARGET/r[1] for r in ROWS),*( (TARGET/r[1]).parent for r in ROWS))):raise ValueError('qwen_custody_exists_no_replay')
        admission=reserve(TARGET,16*1024**3);opened=[]
        try:
            for source,destination,size,expected in ROWS:
                path=TARGET/source
                if path.resolve()!=path:raise ValueError('qwen_custody_redirected_source')
                fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NOATIME);opened.append((fd,path,TARGET/destination,size,expected,None))
                before=fingerprint(os.fstat(fd),size);opened[-1]=(fd,path,TARGET/destination,size,expected,before)
                if fingerprint(path.lstat(),size)!=before or fd_hash(fd)!=expected or fingerprint(os.fstat(fd),size)!=before:raise ValueError('qwen_custody_frozen_source_changed')
            value={'version':1,'state':'copy-intended-no-replay','target_admission':admission,'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'model_activation':False,'iso_inclusion':False,'files':[]}
            save(value)
            for fd,source,destination,size,expected,before in opened:
                if fingerprint(os.fstat(fd),size)!=before or fingerprint(source.lstat(),size)!=before:raise ValueError('qwen_custody_source_changed')
                make_parent(destination.parent)
                copy_one(fd,source,destination,size,expected,before)
                value['files'].append({'source':str(source),'destination':'/'+str(destination.relative_to(TARGET)),'bytes':size,'sha256':expected,'source_metadata':before})
            value['state']='frozen-qualification-copy-verified';save(value)
            return value
        finally:
            for row in opened:os.close(row[0])
    finally:os.close(lease)

if __name__=='__main__':
    if sys.argv[1:]==['host-check']:
        # Execute on physical host BEFORE coordinator dispatch; guest cannot
        # observe the host filesystem. This command does not connect to any VM.
        print(json.dumps({'host_admission':reserve(Path(__file__).resolve(),100*1024**3)}))
    elif sys.argv[1:]==['copy']:print(json.dumps(custody()))
    else:raise SystemExit('usage: qwen_qualification_custody.py host-check|copy')
