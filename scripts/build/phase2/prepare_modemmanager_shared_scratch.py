"""Bind a new private worker directory from existing preallocated build scratch."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess


def manifest(base):
    rows = []
    for p in sorted(base.rglob('*')):
        if 'toddy-editor-workers' in p.relative_to(base).parts:
            continue
        stat = p.lstat()
        value = os.readlink(p) if p.is_symlink() else hashlib.file_digest(p.open('rb'), 'sha256').hexdigest() if p.is_file() else None
        rows.append((str(p.relative_to(base)), stat.st_mode, stat.st_uid, stat.st_gid, value))
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def main():
    assert os.geteuid() == 0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock = open('/var/log/toddy/build/build.lock','a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt = Path('/var/log/toddy/phase2/modemmanager-shared-scratch-1.json')
    assert not receipt.exists() and not receipt.with_suffix('.part').exists(), 'Inspect actual state; never replay preparation'
    base = Path('/mnt/lfs/sources/phase2/work/doxygen-1')
    target = Path('/mnt/lfs/sources/phase2/work/modemmanager-1')
    identity = 'ae4347fb-31fd-4193-a333-0a549e144231'
    assert json.loads(Path('/var/log/toddy/phase2/doxygen-build-volume.json').read_text())['filesystem_uuid'] == identity
    assert subprocess.check_output(['findmnt','-n','-o','UUID','--mountpoint',str(base)],text=True).strip() == identity
    assert base.resolve() == base and target.resolve() == target
    assert not list(target.iterdir()) and subprocess.run(['mountpoint','-q',str(target)]).returncode == 32
    s=os.statvfs('/mnt/lfs');assert s.f_bavail*s.f_frsize>=16*1024**3
    s=os.statvfs(base);assert s.f_bavail*s.f_frsize>=512*1024**2
    before=manifest(base)
    import sys
    sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
    from qualify_libqmi import qualify
    qualify(Path('/opt/toddy-build'))
    native=json.loads(Path('/var/log/toddy/build/b02-libqmi-verify-3.success.json').read_text());assert native['recipe_exit']==native['postcheck_exit']==0
    parent=base/'toddy-editor-workers';assert parent.is_dir() and not parent.is_symlink()
    assert parent.stat().st_uid==0 and parent.stat().st_mode & 0o777==0o700
    worker=parent/'modemmanager-1';worker.mkdir(mode=0o755);os.chown(worker,101,101)
    state={'state':'directory-created','scope':'New private compiler subtree only on existing preallocated Doxygen scratch; no allocation/format/resize/deletion of original cache. Only worker mounted in compiler sandbox.','filesystem_uuid':identity,'source':str(worker),'source_inode':worker.stat().st_ino,'target':str(target),'original_doxygen_manifest_sha256':before}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save()
    subprocess.run(['mount','--bind',str(worker),str(target)],check=True)
    subprocess.run(['mount','-o','remount,bind,nosuid,nodev',str(target)],check=True)
    assert target.stat().st_ino==worker.stat().st_ino and target.stat().st_dev==base.stat().st_dev
    assert manifest(base)==before
    qualify(Path('/opt/toddy-build'))
    state.update(state='mounted',original_doxygen_unchanged=True,recovery='After cold restore verify existing Doxygen UUID and this worker inode, then bind same subtree onto existing empty modemmanager-1 mountpoint. Never recreate, format or replay this preparation.')
    save();print(json.dumps(state))


if __name__=='__main__':main()
