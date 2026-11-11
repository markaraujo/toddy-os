"""Authenticate the isolated rpcgen and Parse::Yapp build artifacts."""
import hashlib
import json
from pathlib import Path

from verify_stage import inspect_stage

BASE = Path('/mnt/lfs/sources')
LOG = Path('/var/log/toddy/phase2')
PROFILES = {
    'rpcsvc-proto': ('rpcsvc-proto-1.4.4',
                     '80a53671aa2291348425660ccdbe7a8a5d48f9c420c04be85fa52206ea04a1a8',
                     '919f1aa37063621cefe80046cb8adcd2553970fe37a1042fa4fe45e90a62efb5'),
    'perl-parse-yapp': ('Parse-Yapp-1.21',
                       'c5a0667d525380757c44cc9edc4ce1d8ddee39362d05a7538dac04e1055514ce',
                       '14dbcd86af9871886b54173ce7c101e1666136aec6a49f1603d824e7f3c2daf9'),
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def qualify(root, name):
    source_dir, manifest_sha, probe_sha = PROFILES[name]
    inputs = BASE / 'phase2/inputs' / source_dir
    work = BASE / 'phase2/work' / (name + '-1')
    recipe_dir = root / 'scripts/build/phase2'
    recipe = recipe_dir / (name + '-build.sh')
    prepared = json.loads((inputs / 'toddy-prepared.json').read_text())
    lock = json.loads((root / 'config/phase2/sources.lock.json').read_text())
    source = next(row for row in lock['components'] if row['name'] == name)
    assert digest(BASE / source['filename']) == prepared['source_sha256'] == source['sha256']
    assert prepared['book_page_sha256'] == source['book_page_sha256'] and not prepared['source_patches']
    assert digest(inputs / 'toddy-build.sh') == prepared['recipe_sha256']
    if name == 'rpcsvc-proto':
        assert prepared['recipe_sha256'] == '3bff61e8fb7fbaef0cd09f2ddde9fb5ebf448fa4b69ebb9a747111c8afc86029'
        assert digest(inputs / 'toddy-probe.c') == prepared['probe_sha256'] == digest(recipe_dir / 'rpcsvc-proto-probe.c')
        suffix = ['bash', '-c', recipe.read_text()]
    else:
        assert prepared['recipe_sha256'] == digest(recipe)
        suffix = ['bash', '/src/toddy-build.sh']

    harness = recipe_dir / 'isolated.sh'
    job_name = name + '-1'
    job = json.loads((LOG / (job_name + '.job.json')).read_text())
    assert job['command'] == ['/bin/bash', str(harness), str(inputs), str(work), *suffix]
    assert job['harness_sha256'] == digest(harness)
    assert (LOG / (job_name + '.exit')).read_text().strip() == '0'
    result = json.loads((work / 'stage-results.json').read_text())
    assert result['version'] == source['version'] and result['compile_exit'] == result['stage_exit'] == 0
    assert digest(work / 'local-probe.log') == probe_sha
    assert result['consumer'] == (work / 'local-probe.log').read_text()
    if name == 'rpcsvc-proto':
        assert result['invalid_source_exit'] > 0 and result['generated_header_recovery_identical']
        assert not result['original_suite_supplied']
    else:
        assert result['upstream_programs'] == 3 and result['upstream_cases'] == 33
        assert digest(work / 'original-tests.log') == '53810fa7d434636ff0af85caa6ff46d998882506308594b6affd01fa01b4fdbe'
    stage = inspect_stage(work / 'stage')
    assert stage['manifest_sha256'] == manifest_sha
    return stage['entries']
