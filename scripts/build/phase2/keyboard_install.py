"""Own the source-authenticated, staged and natively tested keyboard pair."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

from package_copyright import write_copyright
from verify_stage import inspect_stage
from xorg_sdk_build import digest, entries

ROOT=Path('/opt/toddy-build')


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    logs=Path('/var/log/toddy/phase2')
    assert (logs/'keyboard-1.exit').read_text().strip()=='1'
    assert (logs/'keyboard-data-resume-2.exit').read_text().strip()=='0'
    source=Path('/mnt/lfs/sources/phase2/inputs/keyboard-13.1')
    work=Path('/mnt/lfs/sources/phase2/work/keyboard-1')
    assert work.resolve()==work and not (work/'stage').is_symlink()
    config=json.loads((source/'toddy-keyboard.json').read_text())
    assert (source/'toddy-keyboard.json').read_bytes()==(ROOT/'config/phase2/keyboard.lock.json').read_bytes()
    for embedded,canonical in [('toddy-build.sh','keyboard-build.sh'),('toddy-probe.c','keyboard-probe.c')]:
        assert (source/embedded).read_bytes()==(ROOT/'scripts/build/phase2'/canonical).read_bytes()
    prepared=json.loads((source/'toddy-prepared.json').read_text())
    assert prepared['source_patch']['patch_sha256']==config['patch']['sha256']
    assert digest(source/prepared['source_patch']['path'])==prepared['source_patch']['after_sha256']
    job=json.loads((logs/'keyboard-data-resume-2.job.json').read_text())
    assert job['command'][-3:]==['bash','-c',(ROOT/'scripts/build/phase2/keyboard-resume.sh').read_text()]
    assert job['harness_sha256']==digest(ROOT/'scripts/build/phase2/isolated.sh')
    proof=json.loads((work/'qualified.json').read_text())
    assert proof['consumer_exit']==0 and proof['us_br_pt_shift_registry']
    assert proof['unchanged_library_elfs']>26
    assert [(r['name'],r['drivers'],r['exit']) for r in proof['reports']]==[('library',26,0),('locale-recheck',2,0),('data',1,0)]
    for row,directory,base in zip(proof['reports'],['compile-lib','compile-lib','compile-data'],
                                ['keyboard-lib-testlog','keyboard-locale-recheck','keyboard-data-resume']):
        path=work/directory/'meson-logs'/(base+'.json')
        assert row['log_sha256']==digest(path)
        results=[json.loads(line) for line in path.read_text().splitlines()]
        assert len(results)==row['drivers'] and all(r['returncode']==0 and r['result']=='OK' for r in results)
    destinations={};verified={}
    for package in config['packages']:
        name=package['name'];stage=work/'stage'/name
        assert stage.resolve().is_relative_to(work/'stage') and not stage.is_symlink()
        assert entries(stage)==proof['stages'][name]
        verified[name]=inspect_stage(stage)
        destination=Path('/mnt/lfs/sources/stage')/('phase2-'+name)
        assert not destination.exists() and not destination.is_symlink(),'Reconcile prior keyboard transaction; no replay'
        destinations[name]=destination
    (logs/'keyboard-stages.json').write_text(json.dumps(verified,indent=2)+'\n')
    for package in config['packages']:
        name=package['name'];destination=destinations[name]
        shutil.copytree(work/'stage'/name,destination,symlinks=True)
        assert inspect_stage(destination)==verified[name]
        write_copyright(destination,name,[package['archive']])
        depends='' if name=='xkeyboard-config' else 'glibc (>= 2.44-1), libxml2 (>= 2.15.3-1+toddy1), wayland (>= 1.26.0-1+toddy1), xkeyboard-config (= 2.48-1+toddy1)'
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,
                        package['version']+'-1+toddy1',str(destination),'--source',package['archive'],
                        '--recipe','scripts/build/phase2/keyboard-install.sh','--depends',depends,'--install'],cwd=ROOT,check=True)


if __name__=='__main__':main()
