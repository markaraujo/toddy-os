"""Free two byte-verified duplicate metadata stages; retain native compiler/custody."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload
from retire_llvm_stages import digest, verify_package_stage


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    receipt=Path('/var/log/toddy/phase2/gcc-metadata-stage-retirement.json')
    part=receipt.with_suffix('.json.part')
    assert not receipt.exists() and not part.exists(),'Inspect actual retirement state; never replay uncertain deletion'
    version='16.2.0-1+toddy2'
    record_path=Path('/var/log/toddy/packages/gcc_'+version+'_amd64.json')
    record=json.loads(record_path.read_text());assert record['installed'] and record['version']==version
    archive=Path('/var/cache/toddy/packages')/(record_path.stem+'.deb')
    assert record['archive_sha256']=='213faf901ece62e0e7cf5833d1c2a2bae5c39c63a54a67435afef6aa79c0507c'
    assert archive.is_file() and not archive.is_symlink() and digest(archive)==record['archive_sha256']
    native=subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','gcc'],text=True)
    assert native=='install ok installed '+version
    assert '16.2.0' in subprocess.check_output(['chroot','/mnt/lfs','gcc','--version'],text=True)
    stages=[Path('/mnt/lfs/sources/stage')/n for n in ['metadata-gcc','metadata-gcc-16.2.0-1+toddy2']]
    mounts=subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()
    for stage in stages:
        assert stage.resolve()==stage
        assert not any(Path(m)==stage or Path(m).is_relative_to(stage) for m in mounts)
        verify_package_stage(stage,record['payload'])
    state={'scope':'Only two duplicate foundation GCC metadata stages in disposable Phase2 overlay; no installed compiler, source, compiled tests, recovery directory, package/archive or foundation backing deletion',
           'archive':{'path':str(archive),'sha256':record['archive_sha256'],'version':version},
           'record_sha256':digest(record_path),'payload_entries_per_stage':len(record['payload']),
           'before_free_bytes':os.statvfs('/mnt/lfs').f_bavail*os.statvfs('/mnt/lfs').f_frsize,
           'stages':[{'path':str(s),'state':'verified-exact-package-payload'} for s in stages],
           'recovery':'Verify retained canonical archive SHA256, extract to a NEW staging directory; never reinstall compiler or reuse retired staging. Preserve original immutable foundation backing and recovery evidence.'}

    def save():
        with part.open('x') as out:
            json.dump(state,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
        part.replace(receipt)

    save()
    for row in state['stages']:
        row['state']='retiring';save()
        stage=Path(row['path'])
        for name in ['usr','etc']:
            child=stage/name
            if child.exists():
                assert child.is_dir() and not child.is_symlink()
                shutil.rmtree(child)
        (stage/'.toddy-retired.json').write_text(json.dumps({'receipt':str(receipt),'archive':state['archive']},indent=2)+'\n')
        row['state']='retired';save()
    assert all(not (p/'usr').exists() and (p/'.toddy-retired.json').is_file() for p in stages)
    assert digest(archive)==state['archive']['sha256']
    assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','gcc'],text=True)==native
    state['after_free_bytes']=os.statvfs('/mnt/lfs').f_bavail*os.statvfs('/mnt/lfs').f_frsize
    state['state']='complete';save();print(json.dumps(state))


if __name__=='__main__':main()
