"""Own each qualified Python backend independently in one full-root work slice."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from package_copyright import write_copyright
from python_tools_build import digest,stage_entries,wheel_identity
from verify_stage import inspect_stage

ROOT=Path('/opt/toddy-build')
COMMON='python (>= 3.14), python (<< 3.15)'
DEPENDENCIES={
    'calver':COMMON+', setuptools (>= 77)',
    'vcs-versioning':COMMON+', packaging (>= 26.2)',
    'setuptools-scm':COMMON+', vcs-versioning (>= 2.0.0), packaging (>= 20), setuptools (>= 77)',
    'iniconfig':COMMON,'pluggy':COMMON,'poetry-core':COMMON,'pathspec':COMMON,'tomlkit':COMMON,
    'trove-classifiers':COMMON,
    'hatchling':COMMON+', packaging (>= 24.2), pathspec (>= 0.10.1), pluggy (>= 1.0), tomlkit (>= 0.11.1), trove-classifiers',
    'pygments':COMMON,
    'pytest':COMMON+', iniconfig (>= 1.0.1), packaging (>= 22), pluggy (>= 1.5), pluggy (<< 2), pygments (>= 2.7.2)',
}


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    log=Path('/var/log/toddy/phase2')
    assert (log/'python-test-tools-1.exit').read_text().strip()=='0'
    input_=Path('/mnt/lfs/sources/phase2/inputs/python-test-tools-13.1')
    work=Path('/mnt/lfs/sources/phase2/work/python-test-tools-1')
    assert work.resolve()==work and not (work/'stage').is_symlink()
    config=json.loads((input_/'toddy-tools.json').read_text())
    assert (input_/'toddy-tools.json').read_bytes()==(ROOT/'config/phase2/python-test-tools.lock.json').read_bytes()
    assert (input_/'toddy-build.py').read_bytes()==(ROOT/'scripts/build/phase2/python_tools_build.py').read_bytes()
    assert (input_/'toddy-probe.py').read_bytes()==(ROOT/'scripts/build/phase2/python_tools_probe.py').read_bytes()
    record=json.loads((log/'python-test-tools-1.job.json').read_text())
    assert record['command'][-1]=='/src/toddy-build.py'
    proof=json.loads((work/'python-tools/qualified.json').read_text())
    assert proof['probe_exit']==0 and proof['consumer']['uid']==101
    assert proof['config_sha256']==digest(input_/'toddy-tools.json')
    assert proof['probe_log_sha256']==digest(work/'python-tools/probe.log')
    assert proof['consumer']['toml_roundtrip'] and proof['consumer']['lexer_html']
    assert proof['consumer']['pytest']==[
        {'name':'pytest-positive','native_exit':0,'expected_exit':0,'passed':2,'expected_failures':0,'errors':0,'skipped':0},
        {'name':'pytest-negative','native_exit':1,'expected_exit':1,'passed':0,'expected_failures':1,'errors':0,'skipped':0}]
    rows={p['name']:p for p in proof['packages']}
    assert len(rows)==12 and set(rows)==set(DEPENDENCIES)
    stages={};destinations={}
    # Complete every input/stage check before the first native install.
    for package in config['packages']:
        name=package['name'];row=rows[name]
        assert row['version']==package['version'] and row['source_sha256']==package['source_sha256']
        assert proof['consumer']['versions'][name]==package['version']
        wheel=work/row['wheel'].removeprefix('/build/')
        assert wheel.resolve().is_relative_to(work) and not wheel.is_symlink()
        assert digest(wheel)==row['wheel_sha256']
        assert wheel_identity(wheel,name,package['version'])==row['identity']
        assert digest(work/'python-tools/logs'/(name+'.log'))==row['log_sha256']
        for suffix in ['build','install1','install2']:
            assert (work/'python-tools/logs'/(name+'.'+suffix+'.exit')).read_text().strip()=='0'
        source=work/'stage'/name
        assert source.is_dir() and not source.is_symlink() and source.resolve().is_relative_to(work/'stage')
        assert stage_entries(source)==row['entries']
        stages[name]=inspect_stage(source)
        destination=Path('/mnt/lfs/sources/stage')/('phase2-'+name)
        assert not destination.exists() and not destination.is_symlink(), 'Reconcile prior transaction; no install replay'
        destinations[name]=destination
    (log/'python-test-tools-stages.json').write_text(json.dumps(stages,indent=2)+'\n')
    installed=[]
    for package in config['packages']:
        name=package['name'];destination=destinations[name]
        shutil.copytree(work/'stage'/name,destination,symlinks=True)
        assert inspect_stage(destination)==stages[name]
        write_copyright(destination,name,[package['archive']])
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,
                        package['version']+'-1+toddy1',str(destination),
                        '--source',package['archive'],'--recipe','scripts/build/phase2/python-test-tools-install.sh',
                        '--depends',DEPENDENCIES[name],'--install'],cwd=ROOT,check=True)
        installed.append({'name':name,'version':package['version'],'native_backend_exit':0})
        (log/'python-test-tools-installed.partial.json').write_text(json.dumps(installed,indent=2)+'\n')
    (log/'python-test-tools-installed.json').write_text(json.dumps(installed,indent=2)+'\n')


if __name__=='__main__':main()
