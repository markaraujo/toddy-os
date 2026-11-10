"""Require the retained TI-RPC compiler output, unit tests and staged payload."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/libtirpc-1.3.7'
WORK = BASE / 'phase2/work/libtirpc-1'
LOG = Path('/var/log/toddy/phase2')
CONSUMER = 'TI-RPC XDR byte order, truncation refusal and two local recoveries passed\n'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    recipe = root / 'scripts/build/phase2'
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'libtirpc')
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256'] == digest(recipe / 'libtirpc-build.sh')
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe / 'libtirpc-probe.c')
    harness = recipe / 'isolated.sh'
    job = json.loads((LOG / 'libtirpc-1.job.json').read_text())
    assert job['command'] == ['/bin/bash', str(harness), str(INPUT), str(WORK), 'bash', '/src/toddy-build.sh']
    assert job['harness_sha256'] == digest(harness) and (LOG / 'libtirpc-1.exit').read_text().strip() == '0'

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '1.3.7'
    assert not result['original_suite_supplied'] and result['gssapi_linkage']
    assert prepared['source_omissions'] == ['INSTALL -> /usr/share/automake-1.17/INSTALL']
    assert not (INPUT / 'INSTALL').exists() and not (INPUT / 'INSTALL').is_symlink()
    assert digest(WORK / 'stage-shared-links.log') == '8e6be509ea52e890f7edba4d297615c7c69fe7004431419dfc19d13357af945e'
    assert result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER

    compiler = WORK / 'compile'
    artifacts = {str(p.relative_to(compiler)): digest(p) for p in compiler.rglob('*')
                 if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    assert artifacts == result['artifacts']
    encoded = json.dumps(artifacts, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == 'e78c5e36820afefe29e3e0d7aa0a16b1cdefc697861bd8171b2307c728455381'
    stage = inspect_stage(WORK / 'stage')
    assert stage['manifest_sha256'] == 'cad8af60ed7d1bf24db3badb11e132513bcf28f43dcb63e5f8d81b82fbf123da'
    return stage['entries']
