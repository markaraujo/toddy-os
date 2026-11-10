"""Authenticate the frozen staged Keyutils build and select production rules."""
import hashlib
import json
from pathlib import Path
import shutil

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/keyutils-1.6.3'
WORK = BASE / 'phase2/work/keyutils-1'
LOG = Path('/var/log/toddy/phase2')
CONSUMER = 'Keyutils C shared version and build metadata verified\n'
CONFIG = Path('etc/request-key.conf')
EXPECTED_RULES = [
    ['create', 'dns_resolver', '*', '*', '/sbin/key.dns_resolver', '%k'],
    ['negate', '*', '*', '*', '/bin/keyctl', 'negate', '%k', '30', '%S'],
]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def map_digest(entries):
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def production_config(original):
    lines = original.splitlines(keepends=True)
    debug = [line for line in lines if line.split()[:2] == ['create', 'user']]
    assert len(debug) == 6 and all(line.split()[2] in {'debug:*', 'debug:loop:*'} for line in debug)
    retained = [line for line in lines if line not in debug]
    assert [line.split() for line in retained if line.strip() and not line.lstrip().startswith('#')] == EXPECTED_RULES
    return ''.join(retained)


def qualify(root):
    recipe_dir = root / 'scripts/build/phase2'
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'keyutils')
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    assert prepared['source_sha256'] == source['sha256'] == digest(BASE / source['filename'])
    assert not prepared['source_patches'] and prepared['book_page_sha256'] == source['book_page_sha256']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256']
    assert prepared['recipe_sha256'] == '43238fd448149412ce34ea32702952edf78dae5b94e4555f498aaaa9f1ed6c94'
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe_dir / 'keyutils-probe.c')
    harness = recipe_dir / 'isolated.sh'
    job = json.loads((LOG / 'keyutils-1.job.json').read_text())
    assert job['command'] == ['/bin/bash', str(harness), str(INPUT), str(WORK), 'bash', '/src/toddy-build.sh']
    assert job['harness_sha256'] == digest(harness) and (LOG / 'keyutils-1.exit').read_text().strip() == '0'
    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '1.6.3'
    assert result['CXX_header_syntax'] and result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER
    assert result['CLI'] == (WORK / 'keyctl-version.log').read_text() == 'keyctl from keyutils-1.6.3 (Built 2026-11-10)\n'
    for subdir, key, expected in (
        ('compile', 'artifacts', '015ec82b83db0d2934b2a8f4a6b1fa7c55e73a95ab2ab0e88b6c1362c5b23f60'),
        ('stage', 'stage_sha256', '4521fcb9dd71572ff96193de77ad8caef7f9bd3efa47801397228d472ede498c'),
    ):
        base = WORK / subdir
        files = {str(path.relative_to(base)): digest(path)
                 for path in base.rglob('*') if path.is_file() and not path.is_symlink()
                 and (subdir == 'stage' or path.open('rb').read(4) == b'\x7fELF')}
        assert files == result[key] and map_digest(files) == expected
    stage = WORK / 'stage'
    links = {str(path.relative_to(stage)): str(path.readlink()) for path in stage.rglob('*') if path.is_symlink()}
    assert map_digest(links) == 'b6bfc4927883dfac81394ccf2b30053841e21adc4e0aaed0b04b67d0106a8eb3'
    original = (INPUT / 'request-key.conf').read_text()
    assert (stage / CONFIG).read_text() == original
    return result, links, production_config(original)


def promote_config(destination):
    config = destination / CONFIG
    original = config.read_text()
    selected = production_config(original)
    docs = destination / 'usr/share/doc/keyutils'
    docs.mkdir(parents=True)
    (docs / 'request-key.conf.upstream').write_text(original)
    config.write_text(selected)


def prepare_relative_stage():
    original = WORK / 'stage'
    normalized = WORK / 'stage-relative'
    assert not normalized.exists() and not normalized.is_symlink(), 'Reconcile existing normalized stage'
    shutil.copytree(original, normalized, symlinks=True)
    link = normalized / 'usr/lib/libkeyutils.so'
    assert link.readlink() == Path('/usr/lib/libkeyutils.so.1')
    link.unlink()
    link.symlink_to('libkeyutils.so.1')
    return normalized
