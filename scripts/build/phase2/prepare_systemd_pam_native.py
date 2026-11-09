"""Prepare immutable two-driver native cgroup fixture; no installed runtime writes."""
import fcntl,hashlib,json,os,shutil,subprocess
from pathlib import Path
from verify_stage import inspect_stage
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2');WORK=Path('/mnt/lfs/sources/phase2/work/systemd-pam-1')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert (LOG/'systemd-pam-1.exit').read_text().strip()=='1' and (LOG/'systemd-pam-stage-2.exit').read_text().strip()=='0'
    results=json.loads((WORK/'stage-results.json').read_text());assert results['feature_delta']=={'HAVE_PAM':{'old':'0','new':'1'}}
    assert results['compile_exit']==results['stage_exit']==results['staged_version_exit']==results['staged_module_load_exit']==0
    for name,sha in results['artifacts'].items():assert digest(WORK/'stage'/name)==sha
    for name,sha in results['unchanged_selected_artifacts'].items():assert digest(WORK/'compile'/name)==sha
    tests=json.loads((WORK/'compile/meson-info/intro-tests.json').read_text())
    tests=[r for r in tests if r['name'] in ['test-load-fragment','test-unit-serialize']];assert len(tests)==2
    assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+32*1024**2
    fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/systemd-pam-1');receipt=LOG/'systemd-pam-native-prepare-1.json'
    assert not fixture.exists() and not receipt.exists(),'Reconcile existing preparation before any repeat'
    state={'state':'copying','fixture':str(fixture),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':os.getpid()}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(state,indent=2)+'\n');part.replace(receipt)
    save();fixture.mkdir();shutil.copytree(WORK/'stage',fixture/'stage',symlinks=True);assert inspect_stage(WORK/'stage')==inspect_stage(fixture/'stage')
    for name in ['test-load-fragment','test-unit-serialize','src/shared/libsystemd-shared-261.so','src/core/libsystemd-core-261.so']:
        dest=fixture/'compile'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(WORK/'compile'/name,dest)
    shutil.copy2(LOG/'systemd-pam-source-manifest-1.json',fixture/'source-manifest.json')
    shutil.copy2(WORK/'stage-results.json',fixture/'stage-results.json')
    for p in [fixture,*fixture.rglob('*')]:os.chown(p,0,0,follow_symlinks=False)
    artifacts={str(p.relative_to(fixture)):digest(p) for p in fixture.rglob('*') if p.is_file() and not p.is_symlink()}
    accepted={'scope':'Original two cgroup-dependent Systemd driver qualification only; installed runtime remains accepted -PAM until staged update/native boot gates','artifacts':artifacts,'tests':tests,'source':'/sources/systemd-261.2','source_files':7193,'source_manifest_sha256':json.loads((LOG/'systemd-pam-input-1.json').read_text())['source_manifest_sha256'],'stage_artifacts':results['artifacts']}
    (fixture/'accepted.json').write_text(json.dumps(accepted,indent=2)+'\n');state.update(state='complete',manifest_sha256=digest(fixture/'accepted.json'),artifact_files=len(artifacts));save();print(json.dumps(state))
if __name__=='__main__':main()
