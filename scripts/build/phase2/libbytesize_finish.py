"""Correct only the Python API refusal expectation; retain compiler/tests/stage/C."""
from pathlib import Path
import hashlib
import json
import os
import subprocess


def files(base, elf=False):
    return {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in base.rglob('*') if p.is_file() and not p.is_symlink()
            and (not elf or p.open('rb').read(4) == b'\x7fELF')}


def main(recipe):
    work = Path('/build')
    before = work / 'before-finish-2.json'
    assert not before.exists() and not (work / 'stage-results.json').exists()
    assert not (work / 'cli-result.log').exists() and not (work / 'python-consumer.log').exists()
    tests = json.loads((work / 'original-tests.json').read_text())
    assert [(row['name'], row['exit'], row['cases'], row['skipped_count']) for row in tests] == [('core', 0, 32, 1), ('override', 0, 15, 1), ('core-fr', 0, 32, 1)]
    assert (work / 'local-probe.log').read_text() == 'Libbytesize exact binary units/add/divide/big integer/invalid specification/zero division/overflow/two recoveries; no disk access\n'
    artifacts = files(work / 'compile', True)
    stage = files(Path('/stage'))
    logs = {name: hashlib.sha256((work / name).read_bytes()).hexdigest()
            for name in ['configure.log', 'original-build.log', 'original-tests.json', 'test-selection.json',
                         'original-core.log', 'original-override.log', 'original-core-fr.log', 'original-stage.log',
                         'local-probe', 'local-probe.log']}
    assert artifacts and stage
    before.write_text(json.dumps({'artifacts': artifacts, 'stage_sha256': stage, 'retained_logs': logs}, indent=2) + '\n')
    marker = 'export LD_LIBRARY_PATH=/stage/usr/lib PYTHONPATH='
    assert recipe.count(marker) == 1
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', LC_ALL='C.UTF-8')
    subprocess.run(['bash', '-euo', 'pipefail', '-c', recipe[recipe.index(marker):]], env=env, check=True)
    result = json.loads((work / 'stage-results.json').read_text())
    assert result['artifacts'] == artifacts and result['stage_sha256'] == stage
    assert all(hashlib.sha256((work / name).read_bytes()).hexdigest() == sha for name, sha in logs.items())
    (work / 'finish-2-retained.json').write_text(json.dumps({
        'compiler_ELFs_unchanged': len(artifacts), 'stage_files_unchanged': len(stage),
        'retained_log_and_consumer_hashes': logs, 'no_compiler_original_tests_stage_or_C_replay': True,
    }, indent=2) + '\n')
