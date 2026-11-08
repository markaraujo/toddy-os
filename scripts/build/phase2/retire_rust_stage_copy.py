"""Retire one archive-identical Rust SDK stage copy, retaining all usable caches."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from retire_llvm_stages import digest,verify_package_stage


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt=Path('/var/log/toddy/phase2/rust-stage-copy-custody.json');part=receipt.with_suffix('.part')
    assert not receipt.exists() and not part.exists(),'Reconcile prior custody; never replay'
    version='1.97.1-1+toddy1';record_path=Path('/var/log/toddy/packages/rustc_'+version+'_amd64.json')
    record=json.loads(record_path.read_text());assert record['installed']
    archive=Path('/var/cache/toddy/packages')/(record_path.stem+'.deb')
    assert archive.is_file() and not archive.is_symlink()
    assert digest(archive)==record['archive_sha256']=='4db0e6bfec65c41773f54017e6a49aa3c97b2a1e0098ee548284943a4e53cf63'
    stage=Path('/mnt/lfs/sources/stage/phase2-rustc')
    assert stage.resolve()==stage and stage.is_dir() and not stage.is_symlink()
    assert not (stage/'.toddy-retired.json').exists()
    mounts=subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()
    assert not any(Path(m)==stage or Path(m).is_relative_to(stage) for m in mounts)
    verify_package_stage(stage,record['payload'])
    status=subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','rustc'],text=True)
    assert status=='install ok installed '+version
    assert 'rustc 1.97.1' in subprocess.check_output(['chroot','/mnt/lfs','rustc','--version'],text=True)
    assert Path('/mnt/lfs/sources/phase2/work/rustc-1/stage/usr').is_dir()
    state={'scope':'Only duplicate native-package staging copy; installed Rust SDK, original work/stage, compiled tests/caches, sources, native archive, evidence and immutable backings retained',
           'state':'verified','archive':{'path':str(archive),'sha256':record['archive_sha256'],'version':version},
           'record_sha256':digest(record_path),'stage':str(stage),'stage_inode':stage.stat().st_ino,
           'payload_entries':len(record['payload']),'before_free_bytes':shutil.disk_usage('/mnt/lfs').free}
    def save():
        with part.open('x') as f:f.write(json.dumps(state,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();state['state']='retiring';save()
    for name in ['usr','etc']:
        child=stage/name
        if child.exists():
            assert child.is_dir() and not child.is_symlink();shutil.rmtree(child)
    (stage/'.toddy-retired.json').write_text(json.dumps({'receipt':str(receipt),'archive':state['archive']},indent=2)+'\n')
    assert not (stage/'usr').exists() and (stage/'.toddy-retired.json').is_file()
    assert digest(archive)==state['archive']['sha256']
    assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','rustc'],text=True)==status
    state['after_free_bytes']=shutil.disk_usage('/mnt/lfs').free
    state['reclaimed_bytes']=state['after_free_bytes']-state['before_free_bytes']
    state['state']='complete';state['recovery']='Verify retained native archive SHA and extract into a NEW staging directory only if needed; reuse installed SDK/original work cache, never rerun retirement or reinstall.'
    save();print(json.dumps(state))


if __name__=='__main__':main()
