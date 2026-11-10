"""Require the frozen source and exact retained original/recovery stage evidence."""
from pathlib import Path
import hashlib
import json


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    source = Path('/mnt/lfs/sources/phase2/inputs/libbytesize-2.12')
    work = Path('/mnt/lfs/sources/phase2/work/libbytesize-1')
    log = Path('/var/log/toddy/phase2')
    p = json.loads((source / 'toddy-prepared.json').read_text())
    locked = next(row for row in json.loads((root / 'config/phase2/sources.lock.json').read_text())['components'] if row['name'] == 'libbytesize')
    assert p['source_sha256'] == locked['sha256'] == digest(source.parents[2] / locked['filename'])
    assert not p['source_patches'] and p['book_page_sha256'] == locked['book_page_sha256']
    assert digest(source / 'toddy-build.sh') == p['recipe_sha256']
    assert digest(source / 'toddy-probe.c') == p['probe_sha256'] == digest(root / 'scripts/build/phase2/libbytesize-probe.c')
    recipe = (root / 'scripts/build/phase2/libbytesize-build.sh').read_text()
    marker = 'export LD_LIBRARY_PATH=/stage/usr/lib PYTHONPATH='
    assert (source / 'toddy-build.sh').read_text().split(marker, 1)[0] == recipe.split(marker, 1)[0]
    prefix = ['/bin/bash', str(root / 'scripts/build/phase2/isolated.sh'), str(source), str(work)]
    assert json.loads((log / 'libbytesize-1.job.json').read_text())['command'] == prefix + ['bash', '/src/toddy-build.sh']
    assert (log / 'libbytesize-1.exit').read_text().strip() == '1'
    assert 'ValueError: Failed to parse size spec: not a size' in (log / 'libbytesize-1.log').read_text()
    command = (root / 'scripts/build/phase2/libbytesize_finish.py').read_text() + '\nmain(' + repr(recipe) + ')\n'
    assert json.loads((log / 'libbytesize-finish-2.job.json').read_text())['command'] == prefix + ['python3', '-c', command]
    assert (log / 'libbytesize-finish-2.exit').read_text().strip() == '0'
    result = json.loads((work / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '2.12'
    assert [(r['name'], r['exit'], r['cases'], r['skipped_count']) for r in result['original_tests']] == [('core', 0, 32, 1), ('override', 0, 15, 1), ('core-fr', 0, 32, 1)]
    assert result['CLI'] == '1610612736 B\n' and result['python_consumer'] == 'Python exact size arithmetic/malformed refusal/two recoveries\n'
    assert result['consumer'] == (work / 'local-probe.log').read_text()
    before = json.loads((work / 'before-finish-2.json').read_text())
    retained = json.loads((work / 'finish-2-retained.json').read_text())
    assert retained['no_compiler_original_tests_stage_or_C_replay']
    assert retained['retained_log_and_consumer_hashes'] == before['retained_logs']
    assert all(digest(work / name) == sha for name, sha in before['retained_logs'].items())
    for base, key in [('compile', 'artifacts'), ('stage', 'stage_sha256')]:
        actual = {str(p.relative_to(work / base)): digest(p) for p in (work / base).rglob('*')
                  if p.is_file() and not p.is_symlink() and (key != 'artifacts' or p.open('rb').read(4) == b'\x7fELF')}
        assert actual and actual == result[key] == before[key]
    return result
