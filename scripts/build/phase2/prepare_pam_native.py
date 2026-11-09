"""Copy verified nonprivileged PAM stage into a new immutable native fixture."""
import fcntl,hashlib,json,os,shutil,subprocess
from pathlib import Path
from verify_stage import inspect_stage

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    log=Path('/var/log/toddy/phase2');work=Path('/mnt/lfs/sources/phase2/work/pam-1')
    assert (log/'pam-1.exit').read_text().strip()==(log/'pam-password-client-2.exit').read_text().strip()=='0'
    results=json.loads((work/'stage-results.json').read_text())
    assert results['build_exit']==results['stage_exit']==results['consumer_exit']==0
    assert len(results['original_tests'])==77 and all(r['result']=='OK' and r['returncode']==0 for r in results['original_tests'])
    source=Path('/mnt/lfs/sources/phase2/inputs/linux-pam-1.7.2-security-1');canonical=Path('/opt/toddy-build/scripts/build/phase2')
    for a,b in [('toddy-build.sh','pam-build.sh'),('toddy-probe.c','pam-probe.c')]:assert (source/a).read_bytes()==(canonical/b).read_bytes()
    proof=json.loads((work/'password-client-build.json').read_text())
    assert proof['compile_exit']==0 and proof['source_sha256']==digest(canonical/'pam-password-probe.c')
    assert proof['client_sha256']==digest(work/'password-consumer')
    for p,sha in proof['unchanged_original_elfs'].items():assert digest(work/p)==sha
    assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+16*1024**2
    checked=inspect_stage(work/'stage')
    fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/pam-1');receipt=log/'pam-native-prepare-1.json'
    assert not fixture.exists() and not receipt.exists(),'Reconcile actual fixture/receipt; never replay'
    state={'state':'copying','fixture':str(fixture),'stage_manifest_sha256':checked['manifest_sha256'],'pid':os.getpid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:json.dump(state,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();fixture.mkdir();shutil.copytree(work/'stage',fixture/'stage',symlinks=True)
    assert inspect_stage(fixture/'stage')==checked
    shutil.copy2(work/'password-consumer',fixture/'password-consumer')
    for p in [fixture,*fixture.rglob('*')]:os.chown(p,0,0,follow_symlinks=False)
    artifacts={str(p.relative_to(fixture)):digest(p) for p in fixture.rglob('*') if p.is_file() and not p.is_symlink()}
    manifest={'scope':'Copied nonprivileged stage/client; exact setuid helper is enabled only in disposable native overlay for qualification','artifacts':artifacts,'original_elfs_unchanged':len(proof['unchanged_original_elfs']),'original_unit_drivers':77,'stage_manifest_sha256':checked['manifest_sha256'],'privileged_helper':{'path':'/usr/sbin/unix_chkpwd','sha256':artifacts['stage/usr/sbin/unix_chkpwd'],'uid':0,'gid':0,'mode':0o4755},'unqualified':'Actual passwords/privileged helper/session not yet tested'}
    (fixture/'accepted.json').write_text(json.dumps(manifest,indent=2)+'\n')
    state.update(state='complete',artifacts=len(artifacts),manifest_sha256=digest(fixture/'accepted.json'));save();print(json.dumps(state))

if __name__=='__main__':main()
