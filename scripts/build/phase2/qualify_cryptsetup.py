"""Require the retained Cryptsetup compiler output, unit tests and staged payload."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
INPUT = BASE / 'phase2/inputs/cryptsetup-2.8.7'
WORK = BASE / 'phase2/work/cryptsetup-1'
LOG = Path('/var/log/toddy/phase2')
FIXTURE = INPUT / 'tests/luks2_valid_hdr.img.xz'
CONSUMER = 'Cryptsetup LUKS2 metadata refusal and two header reloads passed\n'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root):
    recipe = root / 'scripts/build/phase2'
    prepared = json.loads((INPUT / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == 'cryptsetup')
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    assert digest(INPUT / 'toddy-build.sh') == prepared['recipe_sha256'] == digest(recipe / 'cryptsetup-build.sh')
    assert digest(INPUT / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe / 'cryptsetup-probe.c')
    harness = recipe / 'isolated.sh'
    job = json.loads((LOG / 'cryptsetup-1.job.json').read_text())
    assert job['command'] == ['/bin/bash', str(harness), str(INPUT), str(WORK), 'bash', '/src/toddy-build.sh']
    assert job['harness_sha256'] == digest(harness) and (LOG / 'cryptsetup-1.exit').read_text().strip() == '0'

    result = json.loads((WORK / 'stage-results.json').read_text())
    assert result['compile_exit'] == result['stage_exit'] == 0 and result['version'] == '2.8.7'
    assert result['symbol_checks'] == 155 and result['fixture_bytes_unchanged']
    assert result['original_selected_programs'] == ['vectors-test', 'unit-utils-crypt-test', 'run-all-symbols', 'compat-args-test']
    assert result['device_and_kernel_suites_pending']
    for name, expected in {
        'original-vectors.log': '42f5bd417191ae99da83fbd8d805d2d59bd748ea374672004d231d8d98aab727',
        'original-unit-utils-crypt.log': '431fb956508011213cad316424ea7c969dc402d1eaa9d0de6b525aafbd7e5873',
        'original-symbols.log': '22131a8547dc42bbf3607d93c2708f92f6c9967ece33f4a2622857c93aa39f04',
        'original-compat-args.log': 'da6bbb6758da3811e1156c845785bf0fcbcf12f104210eb8f6a30fa9e3e5b174',
    }.items():
        assert digest(WORK / name) == expected
    assert result['consumer'] == (WORK / 'local-probe.log').read_text() == CONSUMER
    assert digest(FIXTURE) == '7c1932cd9f7c8bc635dd9f04c2ae670744ab7c45167c7464bbd4f236f623a57e'

    compiler = WORK / 'compile'
    artifacts = {str(p.relative_to(compiler)): digest(p) for p in compiler.rglob('*')
                 if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    assert artifacts == result['artifacts']
    encoded = json.dumps(artifacts, sort_keys=True, separators=(',', ':')).encode()
    assert hashlib.sha256(encoded).hexdigest() == 'd51383128a20829716b22b8042bbf594be8fb14304a9a49acf0822fddf5917d4'
    stage = inspect_stage(WORK / 'stage')
    assert stage['manifest_sha256'] == '9fbc00555e2f0d6e2aad570922a7ac27f2b9e3230dc60a20bebdc38a71b60a83'
    return stage['entries']
