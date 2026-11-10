"""Require the retained Popt compiler output, unit tests and staged payload."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/popt-1.19'
WORK = BASE / 'phase2/work/popt-1'
LOG = Path('/var/log/toddy/phase2')
CONSUMER = 'Popt unknown option refusal and two typed argument recoveries passed\n'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    recipe = root / 'scripts/build/phase2'
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'popt')
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256'] == digest(recipe / 'popt-build.sh')
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe / 'popt-probe.c')
    harness = recipe / 'isolated.sh'
    job = json.loads((LOG / 'popt-1.job.json').read_text())
    assert job['command'] == ['/bin/bash', str(harness), str(INPUT), str(WORK), 'bash', '/src/toddy-build.sh']
    assert job['harness_sha256'] == digest(harness) and (LOG / 'popt-1.exit').read_text().strip() == '0'

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '1.19'
    assert result['upstream_nested_cases_passed'] == 65
    assert digest(WORK / 'compile/tests/testit.sh.log') == '71c39aeb4cb7555666fa33bc81eb8f300d47f72bc7e92c31b4e290536a6c8339'
    assert result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER

    compiler = WORK / 'compile'
    artifacts = {str(p.relative_to(compiler)): digest(p) for p in compiler.rglob('*')
                 if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    assert artifacts == result['artifacts']
    encoded = json.dumps(artifacts, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == 'edd90bed54a2c8aae461216834de07f19971e22f18528add39e01ac765ac179d'
    stage = inspect_stage(WORK / 'stage')
    assert stage['manifest_sha256'] == '127a8d77da11c36be5f1f7a41db7fdc736dee5539b62786683c637381bcb5bc0'
    return stage['entries']
