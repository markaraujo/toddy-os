#!/usr/bin/env python3
"""Retire only fixed guest export copies after byte-for-byte host custody."""
import fcntl,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
import phase2_candidate_vm as candidate

ROOT=candidate.ROOT
GENERATIONS=(2,3,4,7)


def guest(source):
    result=subprocess.run(candidate.ssh()+['python3 -'],input=source.encode(),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=300)
    return result.stdout


def inventory_code(generation):
    return f'''import hashlib,json,stat
from pathlib import Path
root=Path("/mnt/lfs/sources/stage/toddy-package-export-{generation}")
assert root.resolve()==root and root.is_dir() and root.stat().st_uid==0
rows={{}}
for path in root.rglob("*"):
 info=path.lstat()
 assert info.st_dev==root.stat().st_dev and not path.is_symlink() and (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))
 if path.is_file():rows[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps(rows,sort_keys=True))
'''


def retire_code(generation,proof,count):
    return f'''import fcntl,hashlib,json,os,shutil,stat,subprocess
from pathlib import Path
subprocess.run(["bash","-c","source /opt/toddy-build/scripts/build/target.sh; guard_target"],check=True)
lock=Path("/var/log/toddy/build/build.lock").open("a");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not list(Path("/var/log/toddy/build").glob("*.running.json")) and not Path("/var/log/toddy/build/input-sync.running").exists()
root=Path("/mnt/lfs/sources/stage/toddy-package-export-{generation}");parent=root.parent
assert root.resolve()==root and root.is_dir() and root.stat().st_uid==0 and root.stat().st_dev==Path("/mnt/lfs").stat().st_dev
rows={{}}
for path in root.rglob("*"):
 info=path.lstat()
 assert info.st_dev==root.stat().st_dev and not path.is_symlink() and (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))
 if path.is_file():rows[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
assert digest=="{proof}" and len(rows)=={count}
assert Path("/mnt/lfs/sources/stage/toddy-package-export-8/archive-export.json").is_file()
receipt=Path("/var/log/toddy/phase2/retire-export{generation}-guest-copy-1.json");assert not receipt.exists()
with receipt.open("x") as stream:
 json.dump({{"state":"retire-intended","profile":"exact-verified-guest-export{generation}-copy","files":{count},"inventory_sha256":digest,"host_copy_verified":True}},stream)
 stream.flush();os.fsync(stream.fileno())
shutil.rmtree(root)
fd=os.open(parent,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
print(json.dumps({{"state":"guest-copy-retired","generation":{generation},"files":{count},"inventory_sha256":digest}}))
'''


def main():
    if sys.argv[1:] or os.geteuid()==0:raise ValueError('Fixed unprivileged no-argument cleanup')
    candidate.owned();candidate.bases()
    with (candidate.vm.VM/'native-boot-test.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for generation in GENERATIONS:
            context=ROOT/'.local/phase2'/f'mvp-package-export-{generation}'
            verified=json.loads((context/'verified.json').read_bytes())
            if (verified.get('state')!='verified-unsigned-export-transfer' or
                    verified.get('source')!=f'/mnt/lfs/sources/stage/toddy-package-export-{generation}'):
                raise ValueError('Exact verified host transfer required')
            rows=json.loads(guest(inventory_code(generation)))
            if (set(rows)!=set(verified['files']) or
                    any(rows[name]!=row['sha256'] for name,row in verified['files'].items()) or
                    rows.get('archive-export.json')!=verified['archive_export_sha256']):
                raise ValueError('Guest export receipt differs from host transfer')
            for name,digest in rows.items():
                if name=='archive-export.json':continue
                path=context/'assets'/name;info=path.lstat()
                if (path.resolve()!=path or not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or
                        info.st_nlink!=1 or hashlib.sha256(path.read_bytes()).hexdigest()!=digest):
                    raise ValueError('Host asset differs: '+name)
            receipt=context/'archive-export.json'
            if receipt.exists():
                if hashlib.sha256(receipt.read_bytes()).hexdigest()!=rows['archive-export.json']:
                    raise ValueError('Retained original export receipt differs')
            else:
                raw=guest(f'import pathlib,sys;sys.stdout.buffer.write(pathlib.Path("/mnt/lfs/sources/stage/toddy-package-export-{generation}/archive-export.json").read_bytes())')
                if hashlib.sha256(raw).hexdigest()!=rows['archive-export.json']:raise ValueError('Original export receipt changed')
                with receipt.open('xb') as stream:
                    os.fchmod(stream.fileno(),0o600);stream.write(raw);stream.flush();os.fsync(stream.fileno())
            proof=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
            result=json.loads(guest(retire_code(generation,proof,len(rows))))
            if result.get('state')!='guest-copy-retired' or result.get('inventory_sha256')!=proof:
                raise ValueError('Guest retirement did not complete')
            print(json.dumps(result,sort_keys=True),flush=True)


if __name__=='__main__':main()
