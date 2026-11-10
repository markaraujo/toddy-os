"""Qualify the retained LibAIO build and its two filesystem test contexts."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/libaio-0.3.113'
WORK = BASE / 'phase2/work/libaio-1'
LOG = Path('/var/log/toddy/phase2')
CONSUMER = 'Linux AIO invalid-depth refusal and two asynchronous file write/read recoveries passed\n'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    recipe = root / 'scripts/build/phase2'
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'libaio')
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256'] == digest(recipe / 'libaio-build.sh')
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe / 'libaio-probe.c')

    harness = recipe / 'isolated.sh'
    prefix = ['/bin/bash', str(harness), str(INPUT), str(WORK)]
    for name, command in (
        ('libaio-1', ['bash', '/src/toddy-build.sh']),
        ('libaio-nowait-1', ['bash', '-c', (recipe / 'libaio-nowait.sh').read_text()]),
    ):
        job = json.loads((LOG / (name + '.job.json')).read_text())
        assert job['command'] == prefix + command and job['harness_sha256'] == digest(harness)
        assert (LOG / (name + '.exit')).read_text().strip() == '0'

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '0.3.113'
    assert result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER
    original = result['original_partcheck']
    assert (original['passed'], original['failed'], original['skipped']) == (18, 0, 1)
    assert original['case_exit_status'] == [[str(case), '3' if case == 21 else '0']
                                             for case in (*range(2, 8), *range(11, 24))]
    assert digest(WORK / 'original-partcheck.log') == '5002cb043b2d211c05fdaf7f49dfca60381f2068c5dea6bf95aea825f7a6dd74'
    assert digest(WORK / 'nowait-21-run.log') == 'c1bef97f6faa2a45dc4abd0acc603945bde2e84ab427484907b4974fe2f4a643'
    compiler = WORK / 'compile'
    artifacts = {str(p.relative_to(compiler)): digest(p) for p in compiler.rglob('*')
                 if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    assert artifacts == result['artifacts']
    encoded = json.dumps(artifacts, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == '0b5686c9a5cb3609208989c8229e3fa461a2f424f69e3c3d5b6d4058cc813d42'
    stage = inspect_stage(WORK / 'stage')
    assert stage['manifest_sha256'] == '44b167f89611a6182604187caed77c09d625e158989c6e8a83c6152c327ab119'
    return stage['entries']
