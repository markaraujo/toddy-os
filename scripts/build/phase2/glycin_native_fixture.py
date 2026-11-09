"""Copy only verified Glycin runtime/test artifacts onto the guarded target."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def manifest(root):
    rows={}
    for p in sorted(root.rglob('*')):
        s=p.lstat();r={'mode':stat.S_IMODE(s.st_mode)}
        if p.is_symlink():r['link']=str(p.readlink())
        elif p.is_file():r.update(sha256=digest(p),bytes=s.st_size)
        else:assert p.is_dir()
        rows[str(p.relative_to(root))]=r
    return rows


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    lock=open('/var/log/toddy/build/build.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(Path('/var/log/toddy/build').glob('*.running.json'))
    for name in ['glycin-1','glycin-tests-1']:
        assert Path('/var/log/toddy/phase2',name+'.exit').read_text().strip()=='0'
    work=Path('/mnt/lfs/sources/phase2/work/glycin-1')
    source=Path('/mnt/lfs/sources/phase2/inputs/glycin-2.1.5/project')
    out=Path('/mnt/lfs/sources/phase2/native-fixtures/glycin-1')
    receipt=Path('/var/log/toddy/phase2/glycin-native-fixture.json')
    assert not receipt.exists() and not out.exists(),'Reconcile prior fixture; never replay'
    tests=json.loads((work/'test-prepare-results.json').read_text())
    stage=json.loads((work/'stage-results.json').read_text())
    assert tests['test_compile_exit']==0 and stage['native_compile_exit']==0
    assert not tests['package_promotable'] and not stage['package_promotable']
    copies=[(work/'stage','stage'),(source/'tests','tests')]
    for row in tests['executables']:
        p=work/Path(row['path']).relative_to('/build')
        assert p.is_file() and not p.is_symlink() and digest(p)==row['sha256']
        copies.append((p,'executables/'+row['name']))
    estimate=sum(p.stat().st_size for root,_ in copies for p in ([root] if root.is_file() else root.rglob('*')) if p.is_file())
    assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+estimate+32*1024**2
    state={'state':'planned','scope':'Copied runtime/test fixture only; no installation or qualification',
           'fixture':str(out),'estimated_payload_bytes':estimate,'tests':tests,'stage':stage}
    def save():
        part=receipt.with_suffix('.part');assert not part.exists()
        with part.open('x') as f:f.write(json.dumps(state,indent=2)+'\n');f.flush();os.fsync(f.fileno())
        part.replace(receipt)
    save();out.parent.mkdir(exist_ok=True);out.mkdir()
    (out/'executables').mkdir()
    for original,relative in copies:
        target=out/relative
        if original.is_dir():
            before=manifest(original);shutil.copytree(original,target,symlinks=True)
            assert manifest(target)==before==manifest(original)
        else:
            shutil.copy2(original,target);assert digest(target)==digest(original)
    for name in ['stage-results.json','test-prepare-results.json']:
        shutil.copy2(work/name,out/name)
    state.update(state='complete',payload=manifest(out),free_target_bytes=shutil.disk_usage('/mnt/lfs').free)
    assert state['free_target_bytes']>=16*1024**3
    save();subprocess.run(['sync'],check=True)
    print(json.dumps({'fixture':str(out),'state':state['state'],'entries':len(state['payload']),
                      'manifest_sha256':hashlib.sha256(json.dumps(state['payload'],sort_keys=True).encode()).hexdigest(),
                      'free_target_bytes':state['free_target_bytes']}))


if __name__=='__main__':main()
