"""Extract one pinned private SDK and prepare browser isolation aliases."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tarfile

BASE=Path('/mnt/lfs/sources/phase2/work/firefox-1')
LOG=Path('/var/log/toddy/phase2')


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt=LOG/'browser-tools-input-1.json'
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(),'Reconcile actual SDK/aliases; never replay'
    volume=json.loads((LOG/'firefox-work-volume-1.json').read_text())
    assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(BASE)],text=True).strip()==volume['filesystem_uuid']
    row=json.loads(Path('/opt/toddy-build/config/phase2/browser-build-tools.lock.json').read_text())['wasi_sdk']
    assert row['version']=='25.0' and row['sha256']=='52640dde13599bf127a95499e61d6d640256119456d1af8897ab6725bcf3d89c'
    tools=BASE/'tools';sdk=tools/'wasi-sdk-25.0-x86_64-linux'
    archive=BASE/'source'/row['filename']
    source=BASE/'source/firefox-153.2.0';source_alias=Path('/mnt/lfs/sources/phase2/inputs/firefox-153.2.0')
    work=BASE/'build/browser-1';work_alias=Path('/mnt/lfs/sources/phase2/work/firefox-build-1')
    assert not any(os.path.lexists(p) for p in [tools,archive,source_alias,work,work_alias])
    state=dict(state='transfer-intended',sdk=row,volume_uuid=volume['filesystem_uuid'],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    def save():
        with receipt.with_suffix('.part').open('x') as f:
            json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        receipt.with_suffix('.part').replace(receipt)
    save();tools.mkdir();h=hashlib.sha256();size=0
    with archive.open('xb') as f:
        while chunk:=sys.stdin.buffer.read(1024**2):
            size+=len(chunk);assert size<=row['bytes'];h.update(chunk);f.write(chunk)
        f.flush();os.fsync(f.fileno())
    assert size==row['bytes'] and h.hexdigest()==row['sha256']
    state['state']='archive-verified';save()
    with tarfile.open(archive) as bundle:
        members=bundle.getmembers()
        assert all(Path(m.name).parts[0]==sdk.name for m in members)
        assert sum(m.size for m in members)<=512*1024**2
        bundle.extractall(tools,filter='data')
    manifest={}
    for p in sdk.rglob('*'):
        name=str(p.relative_to(sdk))
        if p.is_symlink():manifest[name]={'link':os.readlink(p)}
        elif p.is_file():
            with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
            manifest[name]={'sha256':digest,'mode':p.stat().st_mode&0o777}
        else:assert p.is_dir()
    for name in ['bin/clang','bin/clang++','bin/wasm-ld','share/wasi-sysroot/include/wasm32-wasi/c++/v1/cstring']:
        assert (sdk/name).is_file(),name
    inventory=tools/'sdk-inventory.json';inventory.write_text(json.dumps(manifest,sort_keys=True)+'\n')
    subprocess.run(['mount','--bind',str(sdk),str(sdk)],check=True)
    subprocess.run(['mount','-o','remount,bind,ro,nosuid,nodev',str(sdk)],check=True)
    work.mkdir();os.chown(work,101,101)
    for src,dst,readonly in [(source,source_alias,True),(work,work_alias,False)]:
        dst.mkdir();state['pending_bind']=str(dst);save()
        subprocess.run(['mount','--bind',str(src),str(dst)],check=True)
        subprocess.run(['mount','-o','remount,bind,nosuid,nodev,'+('ro' if readonly else 'rw'),str(dst)],check=True)
        assert src.stat().st_ino==dst.stat().st_ino
    state.pop('pending_bind')
    state.update(state='prepared',sdk_directory=str(sdk),inventory_sha256=hashlib.sha256(inventory.read_bytes()).hexdigest(),inventory_entries=len(manifest),source_alias=str(source_alias),work_alias=str(work_alias),scope='SDK extracted but not executed; compiler/isolation qualification pending')
    save();print(json.dumps(state))


if __name__=='__main__':main()
