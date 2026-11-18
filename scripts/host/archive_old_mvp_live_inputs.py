#!/usr/bin/env python3
"""Archive exact old input bundles, prove every member, then retire guest copies."""
import fcntl,hashlib,json,os,stat,subprocess,sys,tarfile
from pathlib import Path
import phase2_candidate_vm as candidate

ROOT=candidate.ROOT
GENERATIONS=(2,3)
HOST_FLOOR=60*1024**3+512*1024**2


def guest(source,timeout=300):
    return subprocess.run(candidate.ssh()+['python3 -'],input=source.encode(),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=timeout).stdout


def inventory_code(generation):
    return f'''import hashlib,json,os,stat
from pathlib import Path
root=Path("/mnt/lfs/sources/stage/toddy-mvp-live-native-inputs-{generation}")
assert root.resolve()==root and root.is_dir() and root.stat().st_uid==0 and root.stat().st_dev==Path("/mnt/lfs").stat().st_dev
rows={{}}
for path in (root,*root.rglob("*")):
 info=path.lstat();assert info.st_dev==root.stat().st_dev and not path.is_symlink() and not os.listxattr(path,follow_symlinks=False)
 relative="." if path==root else path.relative_to(root).as_posix()
 row={{"mode":stat.S_IMODE(info.st_mode),"uid":info.st_uid,"gid":info.st_gid}}
 if stat.S_ISDIR(info.st_mode):row["kind"]="directory"
 elif stat.S_ISREG(info.st_mode) and info.st_nlink==1:
  row["kind"]="regular";row["bytes"]=info.st_size
  with path.open("rb") as stream:row["sha256"]=hashlib.file_digest(stream,"sha256").hexdigest()
 else:raise ValueError("Unexpected input bundle node")
 rows[relative]=row
print(json.dumps(rows,sort_keys=True))
'''


def retire_code(generation,proof,count):
    return f'''import fcntl,hashlib,json,os,shutil,stat,subprocess
from pathlib import Path
subprocess.run(["bash","-c","source /opt/toddy-build/scripts/build/target.sh; guard_target"],check=True)
lock=Path("/var/log/toddy/build/build.lock").open("a");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path("/var/log/toddy/build").glob("*.running.json")) and not Path("/var/log/toddy/build/input-sync.running").exists()
root=Path("/mnt/lfs/sources/stage/toddy-mvp-live-native-inputs-{generation}");parent=root.parent
assert root.resolve()==root and root.is_dir() and root.stat().st_uid==0 and root.stat().st_dev==Path("/mnt/lfs").stat().st_dev
rows={{}}
for path in (root,*root.rglob("*")):
 info=path.lstat();assert info.st_dev==root.stat().st_dev and not path.is_symlink() and not os.listxattr(path,follow_symlinks=False)
 relative="." if path==root else path.relative_to(root).as_posix()
 row={{"mode":stat.S_IMODE(info.st_mode),"uid":info.st_uid,"gid":info.st_gid}}
 if stat.S_ISDIR(info.st_mode):row["kind"]="directory"
 elif stat.S_ISREG(info.st_mode) and info.st_nlink==1:
  row["kind"]="regular";row["bytes"]=info.st_size
  with path.open("rb") as stream:row["sha256"]=hashlib.file_digest(stream,"sha256").hexdigest()
 else:raise ValueError("Unexpected input bundle node")
 rows[relative]=row
digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
assert digest=="{proof}" and len(rows)=={count}
assert Path("/mnt/lfs/sources/stage/toddy-mvp-live-native-inputs-4/input-prepared.json").is_file()
receipt=Path("/var/log/toddy/phase2/retire-mvp-live-inputs{generation}-guest-copy-1.json");assert not receipt.exists()
with receipt.open("x") as stream:
 json.dump({{"state":"retire-intended","generation":{generation},"members":{count},"inventory_sha256":digest,"host_archive_verified":True}},stream)
 stream.flush();os.fsync(stream.fileno())
shutil.rmtree(root)
fd=os.open(parent,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
print(json.dumps({{"state":"guest-input-copy-retired","generation":{generation},"inventory_sha256":digest}}))
'''


def prove_archive(path,base,expected):
    actual={}
    with tarfile.open(path,'r:') as archive:
        for member in archive:
            if member.name==base:relative='.'
            elif member.name.startswith(base+'/'):relative=member.name[len(base)+1:]
            else:raise ValueError('Archive member escaped fixed input bundle')
            if relative in actual or relative not in expected:raise ValueError('Archive duplicate/unexpected member')
            row={'mode':member.mode,'uid':member.uid,'gid':member.gid}
            if member.isdir():row['kind']='directory'
            elif member.isreg():
                row.update(kind='regular',bytes=member.size)
                stream=archive.extractfile(member);assert stream is not None
                digest=hashlib.sha256()
                for block in iter(lambda:stream.read(4*1024**2),b''):digest.update(block)
                row['sha256']=digest.hexdigest()
            else:raise ValueError('Archive contains special/link member')
            actual[relative]=row
    if actual!=expected:raise ValueError('Archive member bytes or metadata differ')


def main():
    if sys.argv[1:] or os.geteuid()==0:raise ValueError('Fixed unprivileged no-argument archival route')
    candidate.owned();candidate.bases()
    with (candidate.vm.VM/'native-boot-test.lock').open('a') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for generation in GENERATIONS:
            name=f'toddy-mvp-live-native-inputs-{generation}'
            context=ROOT/'.local/phase2'/(f'{name}-host-custody-1')
            if context.exists() or context.is_symlink():raise ValueError('Existing/uncertain input custody; no replay')
            expected=json.loads(guest(inventory_code(generation)))
            proof=hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()
            if len(expected)!=678:raise ValueError('Fixed native input bundle member count changed')
            free=os.statvfs(context.parent);available=free.f_bavail*free.f_frsize
            upper=sum(row.get('bytes',0) for row in expected.values())+32*1024**2
            if available<HOST_FLOOR+upper:raise ValueError('Host custody capacity below reserve')
            context.mkdir(mode=0o700)
            part=context/'inputs.tar.part';final=context/'inputs.tar'
            command=candidate.ssh()+[f'tar -C /mnt/lfs/sources/stage -cf - -- {name}']
            with part.open('xb') as output:
                process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                assert process.stdout is not None
                for block in iter(lambda:process.stdout.read(4*1024**2),b''):output.write(block)
                stderr=process.stderr.read() if process.stderr else b''
                if process.wait(timeout=300) or stderr:raise ValueError('Guest input archive export failed')
                output.flush();os.fsync(output.fileno())
            prove_archive(part,name,expected)
            part.rename(final)
            with final.open('rb') as stream:archive_sha=hashlib.file_digest(stream,'sha256').hexdigest()
            receipt={'version':1,'state':'complete-member-byte-metadata-verified','generation':generation,
                'members':len(expected),'inventory_sha256':proof,'archive_sha256':archive_sha,'archive_bytes':final.stat().st_size}
            with (context/'custody.json').open('x') as stream:
                json.dump(receipt,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
            result=json.loads(guest(retire_code(generation,proof,len(expected)),timeout=300))
            if result.get('state')!='guest-input-copy-retired' or result.get('inventory_sha256')!=proof:
                raise ValueError('Guest input retirement did not complete')
            print(json.dumps({**result,'host_archive_sha256':archive_sha},sort_keys=True),flush=True)


if __name__=='__main__':main()
