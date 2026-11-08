"""Promote qualified headless Xorg SDK stages through controlled native archives."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

from package_copyright import write_copyright
from verify_stage import inspect_stage
from xorg_sdk_build import digest, entries

ROOT = Path('/opt/toddy-build')
DEPENDENCIES = {
    'util-macros': '', 'xorgproto': '', 'xcb-proto': 'python (>= 3.14), python (<< 3.15)',
    'xtrans': '', 'libxau': 'glibc (>= 2.44-1)', 'libxdmcp': 'glibc (>= 2.44-1)',
    'libxcb': 'glibc (>= 2.44-1), libxau (= 1.0.12-1+toddy1), libxdmcp (= 1.1.5-1+toddy1)',
    'libx11': 'glibc (>= 2.44-1), libxcb (= 1.17.0-1+toddy1)',
    'libxkbfile': 'glibc (>= 2.44-1), libx11 (= 1.8.13-1+toddy1)',
    'xkbcomp': 'glibc (>= 2.44-1), libx11 (= 1.8.13-1+toddy1), libxkbfile (= 1.2.0-1+toddy1)',
}


def main():
    subprocess.run(['bash','-c','source /opt/toddy-build/scripts/build/target.sh; guard_target'],check=True)
    logs = Path('/var/log/toddy/phase2')
    original_exit = (logs/'xorg-validation-sdk-1.exit').read_text().strip()
    assert original_exit in {'0','1'}
    source = Path('/mnt/lfs/sources/phase2/inputs/xorg-validation-sdk-13.1')
    work = Path('/mnt/lfs/sources/phase2/work/xorg-validation-sdk-1')
    assert work.resolve() == work and not (work/'stage').is_symlink()
    config = json.loads((source/'toddy-sdk.json').read_text())
    assert (source/'toddy-sdk.json').read_bytes() == (ROOT/'config/phase2/xorg-validation-sdk.lock.json').read_bytes()
    for embedded, canonical in [('toddy-build.py','xorg_sdk_build.py')]:
        assert (source/embedded).read_bytes() == (ROOT/'scripts/build/phase2'/canonical).read_bytes()
    recovery = original_exit == '1'
    if recovery:
        assert digest(source/'toddy-probe.py') == '8e49eb7316a647302023a737b019c2678d03de9cb3a6cffffe6b07fb0c715cf7'
        assert (logs/'xorg-sdk-probe-recovery-2.exit').read_text().strip() == '0'
        recovered = Path('/mnt/lfs/sources/phase2/inputs/xorg-sdk-probe-recovery-2')
        assert (recovered/'toddy-sdk.json').read_bytes() == (source/'toddy-sdk.json').read_bytes()
        for embedded, canonical in [('toddy-probe.py','xorg_sdk_probe.py'),('toddy-finish.py','xorg_sdk_finish.py')]:
            assert (recovered/embedded).read_bytes() == (ROOT/'scripts/build/phase2'/canonical).read_bytes()
        recovery_job=json.loads((logs/'xorg-sdk-probe-recovery-2.job.json').read_text())
        assert recovery_job['command'][-2:] == ['python3','/src/toddy-finish.py']
        assert recovery_job['harness_sha256'] == digest(ROOT/'scripts/build/phase2/isolated.sh')
    else:
        assert (source/'toddy-probe.py').read_bytes() == (ROOT/'scripts/build/phase2/xorg_sdk_probe.py').read_bytes()
    job = json.loads((logs/'xorg-validation-sdk-1.job.json').read_text())
    assert job['command'][-2:] == ['python3','/src/toddy-build.py']
    assert job['harness_sha256'] == digest(ROOT/'scripts/build/phase2/isolated.sh')
    proof = json.loads((work/'xorg-sdk/qualified.json').read_text())
    assert proof['config_sha256'] == digest(source/'toddy-sdk.json')
    assert proof['probe_exit'] == 0 and proof['consumer']['uid'] == 101
    if recovery:
        assert (work/'xorg-sdk/probe.exit').read_text().strip() == '1'
        assert (work/'xorg-sdk/compiler-recovery-2.exit').read_text().strip() == '0'
        assert proof['original_probe_log_sha256'] == digest(work/'xorg-sdk/probe.log')
        assert proof['probe_log_sha256'] == digest(work/'xorg-sdk/compiler-recovery-2.log')
    else:
        assert (work/'xorg-sdk/probe.exit').read_text().strip() == '0'
        assert proof['probe_log_sha256'] == digest(work/'xorg-sdk/probe.log')
    assert proof['consumer']['c_api_exit'] == 0 and proof['consumer']['xkbcomp'] == [
        {'name':'valid','actual_exit':0,'expected_exit':0},
        {'name':'invalid','actual_exit':1,'expected_exit':1}]
    rows = {r['name']:r for r in proof['packages']}
    assert len(rows) == 10 and set(rows) == set(DEPENDENCIES)
    stages = {}; destinations = {}
    for package in config['packages']:
        name = package['name']; row = rows[name]
        assert row['version'] == package['version'] and row['source_sha256'] == package['source_sha256']
        assert row['command_exits'] == [0]*len(row['commands']) and len(row['commands']) == 4
        assert row['log_sha256'] == digest(work/'xorg-sdk/logs'/(name+'.log'))
        for number in range(1,5):
            assert (work/'xorg-sdk/logs'/(name+'.command-'+str(number)+'.exit')).read_text().strip() == '0'
        stage = work/'stage'/name
        assert stage.resolve().is_relative_to(work/'stage') and not stage.is_symlink()
        assert entries(stage) == row['entries']
        stages[name] = inspect_stage(stage)
        destination = Path('/mnt/lfs/sources/stage')/('phase2-'+name)
        assert not destination.exists() and not destination.is_symlink(), 'Reconcile prior transaction; no replay'
        destinations[name] = destination
    (logs/'xorg-validation-sdk-stages.json').write_text(json.dumps(stages,indent=2)+'\n')
    installed = []
    for package in config['packages']:
        name = package['name']; destination = destinations[name]
        shutil.copytree(work/'stage'/name,destination,symlinks=True)
        assert inspect_stage(destination) == stages[name]
        write_copyright(destination,name,[package['archive']])
        subprocess.run([sys.executable,str(ROOT/'scripts/build/stage_package.py'),name,
                        package['version']+'-1+toddy1',str(destination),'--source',package['archive'],
                        '--recipe','scripts/build/phase2/xorg-sdk-install.sh',
                        '--depends',DEPENDENCIES[name],'--install'],cwd=ROOT,check=True)
        installed.append({'name':name,'version':package['version'],'native_backend_exit':0})
        (logs/'xorg-validation-sdk-installed.partial.json').write_text(json.dumps(installed,indent=2)+'\n')
    (logs/'xorg-validation-sdk-installed.json').write_text(json.dumps(installed,indent=2)+'\n')


if __name__ == '__main__':
    main()
