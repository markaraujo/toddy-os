"""Require the frozen libnvme build, original suite and retained probe recovery."""
import hashlib
import json
from pathlib import Path

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/libnvme-1.16.2'
WORK = BASE / 'phase2/work/libnvme-1'
LOG = Path('/var/log/toddy/phase2')
CONSUMER = 'NVMe UUID refusal and roundtrip with two fresh local MI contexts passed\n'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def map_digest(entries):
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def qualify(root):
    recipe_dir = root / 'scripts/build/phase2'
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'libnvme')
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    assert prepared['source_sha256'] == source['sha256'] == digest(BASE / source['filename'])
    assert not prepared['source_patches'] and prepared['book_page_sha256'] == source['book_page_sha256']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256'] == '4728a1f86263309acc018fbf5ddd0142a3c067776be538c98f9057518e8d6157'
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe_dir / 'libnvme-probe.c')

    marker = 'cc -Wall -Wextra -Werror /src/toddy-probe.c'
    current = (recipe_dir / 'libnvme-build.sh').read_text()
    assert current.count(marker) == 1
    assert current.split(marker, 1)[0] == (INPUT / 'toddy-build.sh').read_text().split(marker, 1)[0]
    suffix = 'set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\nulimit -c 0\n'
    suffix += marker + current.split(marker, 1)[1]
    harness = recipe_dir / 'isolated.sh'
    prefix = ['/bin/bash', str(harness), str(INPUT), str(WORK)]
    for job, exit_status, command in (
        ('libnvme-1', '1', ['bash', '/src/toddy-build.sh']),
        ('libnvme-probe-2', '0', ['bash', '-c', suffix]),
    ):
        record = json.loads((LOG / f'{job}.job.json').read_text())
        assert record['command'] == prefix + command and record['harness_sha256'] == digest(harness)
        assert (LOG / f'{job}.exit').read_text().strip() == exit_status
    assert 'unused parameter' in (LOG / 'libnvme-1.log').read_text()

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '1.16.2'
    assert result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER
    original = [json.loads(line) for line in (WORK / 'compile/meson-logs/testlog.json').read_text().splitlines()]
    expected = {'libnvme:NBFT-bad-oldspec', 'libnvme:NBFT-random-noise'}
    assert len(original) == 38 and len({row['name'] for row in original}) == 38
    assert all(row['name'].startswith('libnvme:') for row in original)
    assert {row['name'] for row in original if row['result'] == 'EXPECTEDFAIL'} == expected
    assert sum(row['result'] == 'OK' for row in original) == 36
    assert result['tests'] == [{'name': row['name'].removeprefix('libnvme:'), 'result': row['result']} for row in original]

    for subdir, key, expected in (
        ('compile', 'artifacts', '0d5b178f78eceeef791d4d134776fcf9bd75ce6f6e33136424176a187d123181'),
        ('stage', 'stage_sha256', 'bfd66647bda063d31bbe8b93db5230c0c05f47dfe2f8a9d751d86e1fd61fd2f0'),
    ):
        base = WORK / subdir
        files = {str(path.relative_to(base)): digest(path)
                 for path in base.rglob('*') if path.is_file() and not path.is_symlink()
                 and (subdir == 'stage' or path.open('rb').read(4) == b'\x7fELF')}
        assert files == result[key] and map_digest(files) == expected
    stage = WORK / 'stage'
    links = {str(path.relative_to(stage)): str(path.readlink()) for path in stage.rglob('*') if path.is_symlink()}
    assert map_digest(links) == 'bfefdccac9bdbd9c2f05edb73cae05fde43e4e887d00c3c43aae145303475aea'
    return result, links
