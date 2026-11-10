"""Qualify the retained library build and its exact probe-only recovery."""
import hashlib
import json
from pathlib import Path

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/libatasmart-0.19'
WORK = BASE / 'phase2/work/libatasmart-1'
LOG = Path('/var/log/toddy/phase2')
FIXTURES = {
    'ST9160821AS--3.CLH': '540508565ee3255172d0f7f23f6362380f72dab608f446ced5b275282b36962e',
    'WDC_WD5000AAKS--00TMA0-12.01C01': '894a90eaadfe09a637d07c7e813b453ff66a9738977b9259bf6044721fbea97d',
}
LIBRARY_ALIASES = {'usr/lib/libatasmart.so', 'usr/lib/libatasmart.so.4'}
CONSUMER = 'Two upstream SMART blobs parsed, truncation refused, ATA model retained and valid reload passed\n'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def map_digest(entries):
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def qualify(root):
    recipe_dir = root / 'scripts/build/phase2'
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'libatasmart')
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    assert prepared['source_sha256'] == source['sha256'] == digest(BASE / source['filename'])
    assert not prepared['source_patches'] and prepared['book_page_sha256'] == source['book_page_sha256']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256']
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe_dir / 'libatasmart-probe.c')
    for name, sha in FIXTURES.items():
        assert digest(INPUT / 'blob-examples' / name) == sha

    current = (recipe_dir / 'libatasmart-build.sh').read_text()
    corrected = 'cc -Wall -Wextra -Werror -include stddef.h '
    original = 'cc -Wall -Wextra -Werror '
    assert current.count(corrected) == 1
    assert current.replace(corrected, original, 1) == (INPUT / 'toddy-build.sh').read_text()
    suffix = 'set -euo pipefail\nexport PYTHONDONTWRITEBYTECODE=1\nulimit -c 0\n'
    suffix += corrected + current.split(corrected, 1)[1]
    harness = recipe_dir / 'isolated.sh'
    prefix = ['/bin/bash', str(harness), str(INPUT), str(WORK)]
    for job, exit_status, command in (
        ('libatasmart-1', '1', ['bash', '/src/toddy-build.sh']),
        ('libatasmart-probe-2', '0', ['bash', '-c', suffix]),
    ):
        record = json.loads((LOG / f'{job}.job.json').read_text())
        assert record['command'] == prefix + command
        assert record['harness_sha256'] == digest(harness)
        assert (LOG / f'{job}.exit').read_text().strip() == exit_status
    assert 'unknown type name' in (LOG / 'libatasmart-1.log').read_text()
    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '0.19'
    assert not result['original_suite_supplied'] and result['libudev_version'] == '261'
    assert result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER
    for subdir, key, expected in (
        ('compile', 'artifacts', '01543e3d274c107e537c8edc81c9db8f83f949637295861722449243bdc34c50'),
        ('stage', 'stage_sha256', 'cfcb67c968981aa620e285150c3636ccd96b0b75bbde9ba32b469f1fedd93ae5'),
    ):
        base = WORK / subdir
        files = {str(path.relative_to(base)): digest(path)
                 for path in base.rglob('*') if path.is_file() and not path.is_symlink()
                 and (subdir == 'stage' or path.open('rb').read(4) == b'\x7fELF')}
        assert files == result[key] and map_digest(files) == expected
    stage = WORK / 'stage'
    links = {str(path.relative_to(stage)): str(path.readlink()) for path in stage.rglob('*') if path.is_symlink()}
    assert links == dict.fromkeys(LIBRARY_ALIASES, 'libatasmart.so.4.0.5')
    return result
