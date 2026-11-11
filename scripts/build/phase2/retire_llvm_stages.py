"""Retire only verified LLVM stage replicas; retain packages, binaries and evidence."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_package import payload
from verify_stage import inspect_stage


def verify_package_stage(stage, expected, allowed_roots=frozenset({'usr','etc','DEBIAN'})):
    assert stage.is_dir() and not stage.is_symlink()
    actual={p:r for p,r in payload(stage).items() if p!='/DEBIAN' and not p.startswith('/DEBIAN/')}
    assert actual==expected,'Changed/unknown stage payload; preserve for review'
    assert {p.name for p in stage.iterdir()}<=allowed_roots


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    assert os.geteuid()==0
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    log=Path('/var/log/toddy/phase2');build=Path('/var/log/toddy/build')
    lock=(build/'build.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not list(build.glob('*.running.json'))
    success=json.loads((build/'b02-llvm-install.success.json').read_text())
    assert success['recipe_exit']==success['postcheck_exit']==0
    receipt=log/'llvm-stage-retirement.json';part=receipt.with_suffix('.json.part')
    assert not receipt.exists() and not part.exists(),'Reconcile prior retirement; no replay'
    target=Path('/mnt/lfs');stages=[];archives=[]
    for name in ['llvm','llvm-runtime']:
        records=list(Path('/var/log/toddy/packages').glob(name+'_*.json'));assert len(records)==1
        record=json.loads(records[0].read_text());assert record['installed'] and record['version']=='22.1.8-1+toddy1'
        archive=Path('/var/cache/toddy/packages')/(records[0].stem+'.deb')
        assert archive.is_file() and not archive.is_symlink() and digest(archive)==record['archive_sha256']
        status=subprocess.check_output(['chroot',str(target),'/usr/bin/dpkg-query','-W','-f=${Status}',name],text=True)
        assert status=='install ok installed'
        stage=target/'sources/stage'/('phase2-'+name)
        assert stage.resolve()==stage
        verify_package_stage(stage,record['payload'])
        stages.append(stage);archives.append({'name':name,'path':str(archive),'sha256':record['archive_sha256']})
    stage=target/'sources/phase2/work/llvm-1/stage';assert stage.resolve()==stage
    original=json.loads((log/'llvm-stage.json').read_text());assert inspect_stage(stage)==original
    assert {p.name for p in stage.iterdir()}<={'usr','etc'}
    stages.append(stage)
    mounts=subprocess.check_output(['findmnt','-rn','-o','TARGET'],text=True).splitlines()
    assert not any(Path(m)==s or Path(m).is_relative_to(s) for m in mounts for s in stages),'Mounted stage refused'
    state={'scope':'Verified duplicate staging only, no installed payload/source/compile/evidence deletion',
           'archives':archives,'original_stage_manifest_sha256':original['manifest_sha256'],
           'before_free_bytes':os.statvfs(target).f_bavail*os.statvfs(target).f_frsize,
           'stages':[{'path':str(s),'state':'verified'} for s in stages],
           'recovery':'Canonical native archives retained, SHA check before extraction to a new stage. Never rerun an uncertain retirement or install. Retired markers prevent promotion replay.'}

    def save():
        with part.open('x') as out:json.dump(state,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
        part.replace(receipt)

    save()
    for row in state['stages']:
        row['state']='retiring';save();stage=Path(row['path'])
        for name in ['usr','etc']:
            child=stage/name
            if child.exists():
                assert child.is_dir() and not child.is_symlink()
                shutil.rmtree(child)
        (stage/'.toddy-retired.json').write_text(json.dumps({'receipt':str(receipt),'archives':archives},indent=2)+'\n')
        row['state']='retired';save()
    state['after_free_bytes']=os.statvfs(target).f_bavail*os.statvfs(target).f_frsize
    assert all(not (Path(r['path'])/'usr').exists() and (Path(r['path'])/'.toddy-retired.json').is_file() for r in state['stages'])
    state['state']='complete';save()
    print(json.dumps(state))


if __name__=='__main__':main()
