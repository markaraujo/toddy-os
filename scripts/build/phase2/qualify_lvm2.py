"""Require the retained LVM2 compiler output, unit tests and staged payload."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/LVM2.2.03.42'
WORK = BASE / 'phase2/work/lvm2-1'
LOG = Path('/var/log/toddy/phase2')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    recipe = root / 'scripts/build/phase2'
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'lvm2')
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256'] == digest(recipe / 'lvm2-build.sh')
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe / 'lvm2-probe.c')
    harness = recipe / 'isolated.sh'
    job = json.loads((LOG / 'lvm2-1.job.json').read_text())
    assert job['command'] == ['/bin/bash', str(harness), str(INPUT), str(WORK), 'bash', '/src/toddy-build.sh']
    assert job['harness_sha256'] == digest(harness) and (LOG / 'lvm2-1.exit').read_text().strip() == '0'

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '2.03.42'
    assert len(set(result['unit_cases_passed'])) == 156 and result['original_device_tests_pending']
    assert digest(WORK / 'original-unit-run.log') == 'cc0fca9fcf69c843a09380d344513b4d30e4649a7607eee802d0153e463d48d5'
    assert '156/156 tests passed' in (WORK / 'original-unit-run.log').read_text()
    assert result['consumer'] == 'Device Mapper name escapes and two local pool lifecycles passed\n'

    compiler = WORK / 'compile'
    artifacts = {str(p.relative_to(compiler)): digest(p) for p in compiler.rglob('*')
                 if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    assert artifacts == result['artifacts']
    encoded = json.dumps(artifacts, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == 'e3868922136d472c5f4961d3bd874e812fb3ca8d4e18a82f9517e60f2fa24d88'
    stage = inspect_stage(WORK / 'stage')
    assert stage['manifest_sha256'] == '7d6cc86f984f9287c769d4e4ca9646cc3b1f527fc6c4936a16820de2a13e562f'
    return stage['entries']
