"""Verify the frozen UDisks input and exact retained build and test receipts."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/udisks-2.11.2'
WORK = BASE / 'phase2/work/udisks2-1'
LOG = Path('/var/log/toddy/phase2')
CONSUMER = 'UDisks local D-Bus skeleton properties and two object lifecycles passed\n'
GI_CONSUMER = 'UDisks 2 GI metadata and two local manager objects passed\n'

JOBS = {
    'udisks2-1': (2, 'd844c129dbdd43f1ffb3ee211861a62a34eb4523da08825bf78e9c8afd37e64d'),
    'udisks2-no-man-2': (1, '24d78572280d4c6b6ad68c6e02a31fb23fb0c92aa5aed6469875c1a6af76334f'),
    'udisks2-gi-3': (0, 'c7c92780a0ea6d82c69ae253c25645663073e027df00733b2f4bed6c23df816d'),
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    recipe = root / 'scripts/build/phase2'
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'udisks2')
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256'] == '2e06441a1064614a7ade46cd24ae56b1c2d6e4d391aedf5ae7070a063f48f4c2'
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe / 'udisks2-probe.c')
    harness = recipe / 'isolated.sh'
    for name, (exit_status, command_sha) in JOBS.items():
        job = json.loads((LOG / (name + '.job.json')).read_text())
        command = json.dumps(job['command'], separators=(',', ':')).encode()
        assert hashlib.sha256(command).hexdigest() == command_sha
        assert job['harness_sha256'] == digest(harness)
        assert int((LOG / (name + '.exit')).read_text()) == exit_status
    assert 'Attempt to load network entity' in (WORK / 'original-build.log').read_text()
    assert 'ManagerSkeleton' in (LOG / 'udisks2-no-man-2.log').read_text()

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '2.11.2'
    assert len(set(result['original_cases'])) == 23 and result['daemon_activation_and_device_tests_pending']
    assert digest(WORK / 'compile/src/tests/udisks-test.log') == '92b6c8de2e958c0de4afec0b81c073bd4f6efafa2cfc3c36e46b3c265dd2df8e'
    assert result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER
    assert result['gi_consumer'] == (WORK / 'local-gi-3.log').read_text() == GI_CONSUMER

    compiler = WORK / 'compile'
    artifacts = {str(p.relative_to(compiler)): digest(p) for p in compiler.rglob('*')
                 if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    assert artifacts == result['artifacts']
    encoded = json.dumps(artifacts, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == '2fb96b49859a9ec90a12d61a4b9ca381c4b05aa36f5b69d2004d33293a3474f8'
    stage = inspect_stage(WORK / 'stage')
    assert stage['manifest_sha256'] == 'eba2f9ff24bdcac0c60d69a85a7e7b21ce33484b9cdfbb52bc799dd1f86d3053'
    return stage['entries']
