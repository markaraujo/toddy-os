"""Prepare a native client fixture against the installed, not yet boot-qualified delta."""
import fcntl,hashlib,json,os,shutil,subprocess
from pathlib import Path
from install_systemd_pam import verify_installed
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2');WORK=Path('/mnt/lfs/sources/phase2/work/systemd-pam-1')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    run=json.loads(Path('/var/log/toddy/build/b02-systemd-pam-install.success.json').read_text());assert run['recipe_exit']==run['postcheck_exit']==0
    assert (LOG/'systemd-session-client-3.exit').read_text().strip()=='0'
    built=json.loads((WORK/'session-client-build.json').read_text());assert built['compile_exit']==0
    assert built['source_sha256']==digest(ROOT/'scripts/build/phase2/systemd-session-probe.c') and built['client_sha256']==digest(WORK/'session-consumer')
    record=json.loads(Path('/var/log/toddy/packages/systemd_261.2-1+toddy3_amd64.json').read_text());assert record['installed'];verify_installed(record)
    installed={p:row['sha256'] for p,row in record['payload'].items() if p in {'/usr/lib/systemd/systemd','/usr/lib/systemd/systemd-executor','/usr/lib/systemd/libsystemd-core-261.so','/usr/lib/systemd/libsystemd-shared-261.so','/usr/lib/security/pam_systemd.so','/etc/pam.d/systemd-user'}}
    pam=json.loads(Path('/var/log/toddy/packages/linux-pam_1.7.2-1+toddy2_amd64.json').read_text());assert pam['installed']
    for p in ['/usr/lib/libpam.so.0.85.1','/usr/sbin/unix_chkpwd']:
        installed[p]=pam['payload'][p]['sha256'];assert digest(Path('/mnt/lfs')/p.lstrip('/'))==installed[p]
    assert len(installed)==8
    fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/systemd-session-1');receipt=LOG/'systemd-session-native-prepare-1.json'
    assert not fixture.exists() and not receipt.exists(),'Reconcile prior preparation; never replay'
    result={'state':'copying','fixture':str(fixture),'artifact_files':1,'installed_artifacts':len(installed),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:json.dump(result,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();fixture.mkdir();shutil.copy2(WORK/'session-consumer',fixture/'session-consumer');os.chown(fixture/'session-consumer',0,0)
    accepted={'scope':'Actual new-PID1 cold boot/PAMName/logind/user session/recovery fixture; no GNOME acceptance yet','artifacts':{'session-consumer':built['client_sha256']},'installed_artifacts':installed,'native_package_version':record['version'],'client_source_sha256':built['source_sha256']}
    (fixture/'accepted.json').write_text(json.dumps(accepted,indent=2)+'\n')
    result.update(state='complete',manifest_sha256=digest(fixture/'accepted.json'));save();print(json.dumps(result))
if __name__=='__main__':main()
