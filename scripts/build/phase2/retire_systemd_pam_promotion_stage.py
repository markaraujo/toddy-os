"""Retire only the new boot-qualified Systemd full-package promotion replica."""
import fcntl,json,os,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_step import snapshot
from retire_llvm_stages import digest
from stage_package import payload

def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    log=Path('/var/log/toddy/phase2');receipt=log/'systemd-pam-promotion-stage-custody-1.json'
    assert not receipt.exists(),'Reconcile actual retirement; never replay'
    accepted=json.loads((log/'systemd-session-acceptance-1.json').read_text());assert accepted['state']=='native-boot-session-qualified'
    record_path=Path('/var/log/toddy/packages/systemd_261.2-1+toddy3_amd64.json');record=json.loads(record_path.read_text());assert record['installed']
    archive=Path('/var/cache/toddy/packages/systemd_261.2-1+toddy3_amd64.deb');expected='c059a1dd232a3655da4a67f662e01932bec81d9855cd33ef4b8ca6141de96b90'
    assert digest(archive)==record['archive_sha256']==expected
    assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','systemd'],text=True)=='install ok installed 261.2-1+toddy3'
    stage=Path('/mnt/lfs/sources/stage/phase2-systemd-pam-3');assert stage.resolve()==stage and not stage.is_symlink()
    assert {p.name for p in stage.iterdir()}=={'usr','etc','var','DEBIAN'}
    assert {p:r for p,r in payload(stage).items() if p!='/DEBIAN' and not p.startswith('/DEBIAN/')}==record['payload']
    assert Path('/mnt/lfs/sources/phase2/work/systemd-pam-1/stage/usr').is_dir()
    mounts=[Path(m) for m in subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()]
    assert not any(m==stage or m.is_relative_to(stage) for m in mounts)
    before=snapshot()
    state={'state':'verified','scope':'Only new full-package promotion replica, after actual new-PID1/session recovery qualification; installed files/original six-file compiler stage/source/tests/both archives retained','stage':str(stage),'stage_inode':stage.stat().st_ino,'archive':str(archive),'archive_sha256':expected,'record_sha256':digest(record_path),'payload_entries':len(record['payload']),'before_free_bytes':shutil.disk_usage('/mnt/lfs').free}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();assert stage.stat().st_ino==state['stage_inode'];state['state']='retiring';save()
    for name in ['usr','etc','var']:
        p=stage/name;assert p.is_dir() and not p.is_symlink();shutil.rmtree(p)
    (stage/'.toddy-retired.json').write_text(json.dumps({'receipt':str(receipt),'archive':str(archive),'archive_sha256':expected},indent=2)+'\n')
    assert snapshot()==before,'Installed root changed; preserve archives and diagnose'
    state.update(state='complete',installed_root_changed_paths=0,after_free_bytes=shutil.disk_usage('/mnt/lfs').free,recovery='Verify retained native archive/record and extract to a NEW stage if needed; never reinstall or replay retirement. Original compiler stage/source/raw evidence remain.')
    state['reclaimed_bytes']=state['after_free_bytes']-state['before_free_bytes'];save();print(json.dumps({k:state[k] for k in ['state','reclaimed_bytes','installed_root_changed_paths']}))
if __name__=='__main__':main()
