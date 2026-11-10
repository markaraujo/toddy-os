"""Verify the retained Libblockdev build, tests, and two evidence recoveries."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/libblockdev-3.5.0'
WORK = BASE / 'phase2/work/libblockdev-1'
LOG = Path('/var/log/toddy/phase2')
CONSUMER = 'BlockDev 3 GI and two local crypto plugin load/query/unload cycles passed'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    recipe = root / 'scripts/build/phase2'
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'libblockdev')
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    original = INPUT / 'toddy-build.sh'
    assert digest(original) == prepared['recipe_sha256'] == 'c2aa9f8da06efc3e57ee1f55927c09c340cac08f2093f559d2732d2736857655'
    current = (recipe / 'libblockdev-build.sh').read_text()
    marker = 'export GI_TYPELIB_PATH=/stage/usr/lib/girepository-1.0'
    assert current.split(marker, 1)[0] == original.read_text().split(marker, 1)[0]
    _, tail = current.split(marker, 1)
    probe = 'set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1\nulimit -c 0\n'
    probe += marker + tail.replace('/build/local-probe.log', '/build/local-probe-2.log')
    collector_marker = "python3 - <<'PYTEST'"
    collector = 'set -euo pipefail\n' + collector_marker + current.split(collector_marker, 1)[1].replace(
        "'local-probe.log'", "'local-probe-2.log'")

    harness = recipe / 'isolated.sh'
    prefix = ['/bin/bash', str(harness), str(INPUT), str(WORK)]
    for name, status, command in (
        ('libblockdev-1', '1', ['bash', '/src/toddy-build.sh']),
        ('libblockdev-probe-2', '1', ['bash', '-c', probe]),
        ('libblockdev-collect-3', '0', ['bash', '-c', collector]),
    ):
        job = json.loads((LOG / (name + '.job.json')).read_text())
        assert job['command'] == prefix + command and job['harness_sha256'] == digest(harness)
        assert (LOG / (name + '.exit')).read_text().strip() == status

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '3.5.0'
    assert result['selected_original_core_cases'] == 3 and result['device_tests_pending']
    assert digest(WORK / 'original-core-tests.log') == '69ab95d2501e23853ac1519300722ce43fa70d35c372f9790cdb016743ec7d3e'
    assert digest(WORK / 'local-probe-2.log') == '7ba20aefaef09ca9e470998feacd6a8559db877b5dd2c4f9f8b244da5d620a5b'
    assert result['consumer'] == (WORK / 'local-probe-2.log').read_text()
    assert result['consumer'].splitlines()[-1] == CONSUMER

    compiler = WORK / 'compile'
    artifacts = {str(p.relative_to(compiler)): digest(p) for p in compiler.rglob('*')
                 if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    assert artifacts == result['artifacts']
    encoded = json.dumps(artifacts, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == '9ff7b20e40d97dad7622a247cea138631f0170ee6306b7a3765f9dfafd4b221c'
    stage = inspect_stage(WORK / 'stage')
    assert stage['manifest_sha256'] == '823c77026558533040aa1977e9cdaaa11b2830b4cb895e5d66345eb0c3fbb8d1'
    return stage['entries']
