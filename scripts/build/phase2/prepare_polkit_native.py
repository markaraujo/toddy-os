"""Freeze existing full-build artifacts/source for native original tests, no install."""
import fcntl,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path('/opt/toddy-build');LOG=Path('/var/log/toddy/phase2')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    assert (LOG/'polkit-full-1.exit').read_text().strip()=='0'
    source=Path('/mnt/lfs/sources/phase2/inputs/polkit-127-full-1');work=Path('/mnt/lfs/sources/phase2/work/polkit-full-1')
    assert (source/'toddy-build.sh').read_bytes()==(ROOT/'scripts/build/phase2/polkit-full-build.sh').read_bytes()
    proof=json.loads((work/'stage-results.json').read_text());assert proof['compile_exit']==proof['stage_exit']==0 and not proof['package_promotable']
    patch=json.loads((ROOT/'config/phase2/polkit-patches.lock.json').read_text());assert digest(source/patch['source_file'])==patch['after_sha256']
    assert len(proof['original_tests'])==5
    for base,key in [(work/'compile','artifacts'),(work/'stage','stage_sha256')]:
        for name,sha in proof[key].items():assert digest(base/name)==sha
    fixture=Path('/mnt/lfs/sources/phase2/native-fixtures/polkit-suite-1');receipt=LOG/'polkit-native-prepare-1.json'
    assert not fixture.exists() and not receipt.exists(),'Reconcile fixture before any repeat'
    files={}
    for base in [source,work]:
        for p in base.rglob('*'):
            if p.is_symlink():files[str(p.relative_to('/mnt/lfs'))]={'symlink':str(p.readlink())}
            elif p.is_file():files[str(p.relative_to('/mnt/lfs'))]={'sha256':digest(p)}
    fixture.mkdir()
    accepted={'scope':'Five original Polkit drivers only; mock backend fixtures, not actual system authorization','source':str(source.relative_to('/mnt/lfs')),'work':str(work.relative_to('/mnt/lfs')),'files':files,'tests':proof['original_tests'],'patch':patch}
    (fixture/'accepted.json').write_text(json.dumps(accepted,indent=2)+'\n')
    receipt.write_text(json.dumps({'state':'complete','fixture':str(fixture),'manifest_sha256':digest(fixture/'accepted.json'),'artifact_files':len(files)},indent=2)+'\n')
    print(receipt.read_text())
if __name__=='__main__':main()
